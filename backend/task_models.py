"""
Database models for Trio task management.
Uses SQLAlchemy 2.0 style with proper type hints.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database_improved import Base


class TaskCategory(Base):
    """Category model for organizing tasks."""
    __tablename__ = "task_categories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationship to tasks
    tasks: Mapped[list["TrioTask"]] = relationship("TrioTask", back_populates="category")


class TrioTask(Base):
    """Main task model for Trio task management."""
    __tablename__ = "trio_tasks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trio_task_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True)  # External Trio ID
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, in_progress, completed, cancelled
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high, urgent
    
    # Assignment
    assigned_to: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # TrioID
    assigned_to_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)  # TrioID
    created_by_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Category relationship
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("task_categories.id"), nullable=True)
    category: Mapped[Optional["TaskCategory"]] = relationship("TaskCategory", back_populates="tasks")
    
    # Queue/Service association
    service_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    service_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Additional metadata
    is_synced: Mapped[bool] = mapped_column(Boolean, default=False)  # Whether synced with Trio API
    sync_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Last sync error if any
    metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON field for extra data
    
    def __repr__(self) -> str:
        return f"<TrioTask(id={self.id}, title='{self.title}', status='{self.status}')>"


class TaskComment(Base):
    """Comments/notes for tasks."""
    __tablename__ = "task_comments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("trio_tasks.id"), nullable=False)
    author_id: Mapped[str] = mapped_column(String(100), nullable=False)  # TrioID
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationship to task
    task: Mapped["TrioTask"] = relationship("TrioTask", backref="comments")
    
    def __repr__(self) -> str:
        return f"<TaskComment(id={self.id}, task_id={self.task_id}, author='{self.author_name}')>"


class TaskHistory(Base):
    """History/audit log for task changes."""
    __tablename__ = "task_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("trio_tasks.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # created, updated, status_changed, assigned, etc.
    field_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    performed_by: Mapped[str] = mapped_column(String(100), nullable=False)  # TrioID
    performed_by_name: Mapped[str] = mapped_column(String(255), nullable=False)
    performed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationship to task
    task: Mapped["TrioTask"] = relationship("TrioTask", backref="history")
    
    def __repr__(self) -> str:
        return f"<TaskHistory(id={self.id}, task_id={self.task_id}, action='{self.action}')>"
