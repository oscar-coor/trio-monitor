"""
Task API endpoints for Trio task management.
Uses FastAPI with Pydantic v2 models for validation.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, ConfigDict
from database_improved import get_db
from task_service import TaskService
from task_models import TrioTask, TaskCategory, TaskComment

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


# Pydantic v2 models for API
class TaskCreateRequest(BaseModel):
    """Request model for creating a task."""
    model_config = ConfigDict(from_attributes=True)
    
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    status: str = Field(default="pending", pattern="^(pending|in_progress|completed|cancelled)$")
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    category_id: Optional[int] = None
    service_id: Optional[str] = None
    service_name: Optional[str] = None
    due_date: Optional[datetime] = None
    created_by: str
    created_by_name: str


class TaskUpdateRequest(BaseModel):
    """Request model for updating a task."""
    model_config = ConfigDict(from_attributes=True)
    
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed|cancelled)$")
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    category_id: Optional[int] = None
    service_id: Optional[str] = None
    service_name: Optional[str] = None
    due_date: Optional[datetime] = None
    updated_by: str
    updated_by_name: str


class TaskResponse(BaseModel):
    """Response model for a task."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    trio_task_id: Optional[str]
    title: str
    description: Optional[str]
    status: str
    priority: str
    assigned_to: Optional[str]
    assigned_to_name: Optional[str]
    created_by: str
    created_by_name: str
    category_id: Optional[int]
    service_id: Optional[str]
    service_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    is_synced: bool
    sync_error: Optional[str]


class CommentCreateRequest(BaseModel):
    """Request model for adding a comment."""
    model_config = ConfigDict(from_attributes=True)
    
    content: str = Field(..., min_length=1)
    author_id: str
    author_name: str


class CommentResponse(BaseModel):
    """Response model for a comment."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    task_id: int
    author_id: str
    author_name: str
    content: str
    created_at: datetime


class CategoryResponse(BaseModel):
    """Response model for a category."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str]
    created_at: datetime


class TaskListResponse(BaseModel):
    """Response model for task list with pagination."""
    model_config = ConfigDict(from_attributes=True)
    
    tasks: List[TaskResponse]
    total: int
    limit: int
    offset: int


# Task endpoints
@router.post("/", response_model=TaskResponse)
async def create_task(
    request: TaskCreateRequest,
    db: Session = Depends(get_db)
) -> TaskResponse:
    """Create a new task."""
    service = TaskService(db)
    task = service.create_task(
        title=request.title,
        description=request.description,
        priority=request.priority,
        status=request.status,
        created_by=request.created_by,
        created_by_name=request.created_by_name,
        assigned_to=request.assigned_to,
        assigned_to_name=request.assigned_to_name,
        category_id=request.category_id,
        service_id=request.service_id,
        service_name=request.service_name,
        due_date=request.due_date
    )
    return TaskResponse.model_validate(task)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db)
) -> TaskResponse:
    """Get a specific task by ID."""
    service = TaskService(db)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse.model_validate(task)


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = Query(None, pattern="^(pending|in_progress|completed|cancelled)$"),
    priority: Optional[str] = Query(None, pattern="^(low|medium|high|urgent)$"),
    assigned_to: Optional[str] = None,
    created_by: Optional[str] = None,
    service_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
) -> TaskListResponse:
    """List tasks with optional filters."""
    service = TaskService(db)
    tasks = service.list_tasks(
        status=status,
        priority=priority,
        assigned_to=assigned_to,
        created_by=created_by,
        service_id=service_id,
        limit=limit,
        offset=offset
    )
    
    # Get total count (simplified - in production would use a count query)
    total = len(tasks)
    
    return TaskListResponse(
        tasks=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
        limit=limit,
        offset=offset
    )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    request: TaskUpdateRequest,
    db: Session = Depends(get_db)
) -> TaskResponse:
    """Update a task."""
    service = TaskService(db)
    
    # Build update kwargs from request
    update_data = request.model_dump(exclude_unset=True, exclude={"updated_by", "updated_by_name"})
    
    task = service.update_task(
        task_id=task_id,
        updated_by=request.updated_by,
        updated_by_name=request.updated_by_name,
        **update_data
    )
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """Delete a task."""
    service = TaskService(db)
    success = service.delete_task(task_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"message": "Task deleted successfully", "task_id": task_id}


# Comment endpoints
@router.post("/{task_id}/comments", response_model=CommentResponse)
async def add_comment(
    task_id: int,
    request: CommentCreateRequest,
    db: Session = Depends(get_db)
) -> CommentResponse:
    """Add a comment to a task."""
    service = TaskService(db)
    comment = service.add_comment(
        task_id=task_id,
        author_id=request.author_id,
        author_name=request.author_name,
        content=request.content
    )
    
    if not comment:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return CommentResponse.model_validate(comment)


@router.get("/{task_id}/comments", response_model=List[CommentResponse])
async def get_comments(
    task_id: int,
    db: Session = Depends(get_db)
) -> List[CommentResponse]:
    """Get comments for a task."""
    service = TaskService(db)
    task = service.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    comments = db.query(TaskComment).filter(TaskComment.task_id == task_id).order_by(TaskComment.created_at).all()
    return [CommentResponse.model_validate(c) for c in comments]


# Category endpoints
@router.get("/categories/", response_model=List[CategoryResponse])
async def list_categories(
    db: Session = Depends(get_db)
) -> List[CategoryResponse]:
    """List all task categories."""
    categories = db.query(TaskCategory).order_by(TaskCategory.name).all()
    return [CategoryResponse.model_validate(c) for c in categories]


@router.post("/categories/", response_model=CategoryResponse)
async def create_category(
    name: str,
    description: Optional[str] = None,
    db: Session = Depends(get_db)
) -> CategoryResponse:
    """Create a new task category."""
    category = TaskCategory(name=name, description=description)
    db.add(category)
    db.commit()
    db.refresh(category)
    return CategoryResponse.model_validate(category)


# Sync endpoint
@router.post("/sync")
async def sync_with_trio(
    db: Session = Depends(get_db)
) -> dict:
    """Trigger sync with Trio API."""
    service = TaskService(db)
    synced_count = service.sync_tasks_from_trio()
    return {
        "message": "Sync completed",
        "synced_tasks": synced_count
    }
