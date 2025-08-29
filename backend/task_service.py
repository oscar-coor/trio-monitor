"""
Task service layer for Trio task management.
Handles business logic and Trio API integration.
"""
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from task_models import TrioTask, TaskCategory, TaskComment, TaskHistory
from database_improved import get_db
from api_client import TrioAPIClient
from config_improved import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TaskService:
    """Service for managing Trio tasks."""
    
    def __init__(self, db: Session, api_client: Optional[TrioAPIClient] = None):
        self.db = db
        self.api_client = api_client or TrioAPIClient()
    
    def create_task(
        self,
        title: str,
        created_by: str,
        created_by_name: str,
        description: Optional[str] = None,
        priority: str = "medium",
        status: str = "pending",
        assigned_to: Optional[str] = None,
        assigned_to_name: Optional[str] = None,
        category_id: Optional[int] = None,
        service_id: Optional[str] = None,
        service_name: Optional[str] = None,
        due_date: Optional[datetime] = None,
        sync_to_trio: bool = True
    ) -> TrioTask:
        """Create a new task."""
        task = TrioTask(
            title=title,
            description=description,
            status=status,
            priority=priority,
            created_by=created_by,
            created_by_name=created_by_name,
            assigned_to=assigned_to,
            assigned_to_name=assigned_to_name,
            category_id=category_id,
            service_id=service_id,
            service_name=service_name,
            due_date=due_date
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        # Record history
        self._add_history(
            task_id=task.id,
            action="created",
            performed_by=created_by,
            performed_by_name=created_by_name
        )
        
        # Sync to Trio API if enabled
        if sync_to_trio:
            try:
                trio_response = self._sync_task_to_trio(task)
                if trio_response and "id" in trio_response:
                    task.trio_task_id = str(trio_response["id"])
                    task.is_synced = True
                    self.db.commit()
            except Exception as e:
                logger.error(f"Failed to sync task to Trio: {e}")
                task.sync_error = str(e)
                self.db.commit()
        
        return task
    
    def get_task(self, task_id: int) -> Optional[TrioTask]:
        """Get a task by ID."""
        return self.db.query(TrioTask).filter(TrioTask.id == task_id).first()
    
    def list_tasks(
        self,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        created_by: Optional[str] = None,
        priority: Optional[str] = None,
        service_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TrioTask]:
        """List tasks with optional filters."""
        query = self.db.query(TrioTask)
        
        if status:
            query = query.filter(TrioTask.status == status)
        if assigned_to:
            query = query.filter(TrioTask.assigned_to == assigned_to)
        if created_by:
            query = query.filter(TrioTask.created_by == created_by)
        if priority:
            query = query.filter(TrioTask.priority == priority)
        if service_id:
            query = query.filter(TrioTask.service_id == service_id)
        
        return query.order_by(desc(TrioTask.created_at)).limit(limit).offset(offset).all()
    
    def update_task(
        self,
        task_id: int,
        updated_by: str,
        updated_by_name: str,
        **kwargs
    ) -> Optional[TrioTask]:
        """Update a task."""
        task = self.get_task(task_id)
        if not task:
            return None
        
        # Update fields
        for field, value in kwargs.items():
            if hasattr(task, field) and value is not None:
                old_value = getattr(task, field)
                if old_value != value:
                    setattr(task, field, value)
                    self._add_history(
                        task_id=task.id,
                        action="updated",
                        field_name=field,
                        old_value=str(old_value),
                        new_value=str(value),
                        performed_by=updated_by,
                        performed_by_name=updated_by_name
                    )
        
        if kwargs.get("status") == "completed":
            task.completed_at = datetime.utcnow()
        
        task.updated_at = datetime.utcnow()
        self.db.commit()
        
        # Sync to Trio if task was previously synced
        if task.trio_task_id:
            try:
                self._sync_task_to_trio(task, is_update=True)
                task.is_synced = True
                task.sync_error = None
                self.db.commit()
            except Exception as e:
                logger.error(f"Failed to sync update to Trio: {e}")
                task.sync_error = str(e)
                self.db.commit()
        
        return task
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task."""
        task = self.get_task(task_id)
        if not task:
            return False
        
        # Delete related records
        self.db.query(TaskComment).filter(TaskComment.task_id == task_id).delete()
        self.db.query(TaskHistory).filter(TaskHistory.task_id == task_id).delete()
        
        # Delete task from Trio if synced
        if task.trio_task_id:
            try:
                self._delete_task_from_trio(task.trio_task_id)
            except Exception as e:
                logger.error(f"Failed to delete from Trio: {e}")
        
        self.db.delete(task)
        self.db.commit()
        return True
    
    def add_comment(
        self,
        task_id: int,
        author_id: str,
        author_name: str,
        content: str
    ) -> Optional[TaskComment]:
        """Add a comment to a task."""
        task = self.get_task(task_id)
        if not task:
            return None
        
        comment = TaskComment(
            task_id=task_id,
            author_id=author_id,
            author_name=author_name,
            content=content
        )
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        
        self._add_history(
            task_id=task_id,
            action="comment_added",
            performed_by=author_id,
            performed_by_name=author_name
        )
        
        return comment
    
    def _add_history(
        self,
        task_id: int,
        action: str,
        performed_by: str,
        performed_by_name: str,
        field_name: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None
    ):
        """Add history entry for a task."""
        history = TaskHistory(
            task_id=task_id,
            action=action,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            performed_by=performed_by,
            performed_by_name=performed_by_name
        )
        self.db.add(history)
        self.db.commit()
    
    def _sync_task_to_trio(self, task: TrioTask, is_update: bool = False) -> Optional[Dict[Any, Any]]:
        """Sync task to Trio API."""
        # This would integrate with actual Trio API
        # Placeholder implementation
        logger.info(f"{'Updating' if is_update else 'Creating'} task in Trio: {task.title}")
        return {"id": f"TRIO-{task.id}"}
    
    def _delete_task_from_trio(self, trio_task_id: str) -> bool:
        """Delete task from Trio API."""
        # Placeholder for Trio API integration
        logger.info(f"Deleting task from Trio: {trio_task_id}")
        return True
    
    def sync_tasks_from_trio(self) -> int:
        """Sync tasks from Trio API."""
        # Placeholder for pulling tasks from Trio
        logger.info("Syncing tasks from Trio API")
        return 0
