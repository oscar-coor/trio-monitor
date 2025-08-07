"""Data models for Trio Monitor application."""

from datetime import datetime, date, time
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent status enumeration."""
    AVAILABLE = "available"
    BUSY = "busy"
    UNAVAILABLE = "unavailable"
    BREAK = "break"
    TRAINING = "training"


class QueueStatus(str, Enum):
    """Queue status based on wait time."""
    GOOD = "good"      # < 15 seconds
    WARNING = "warning"  # 15-20 seconds
    CRITICAL = "critical"  # > 20 seconds


class AgentState(BaseModel):
    """Agent state model."""
    agent_id: str
    name: str
    status: AgentStatus
    current_call_duration: Optional[int] = None
    calls_handled_today: int = 0
    average_call_time: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.now)


class QueueMetrics(BaseModel):
    """Queue metrics model."""
    queue_id: str
    queue_name: str
    current_wait_time: int  # seconds
    queue_depth: int
    status: QueueStatus
    calls_waiting: int
    longest_wait_time: int
    average_wait_time: float
    last_updated: datetime = Field(default_factory=datetime.now)


class ServiceLevelMetrics(BaseModel):
    """Service level metrics data model."""
    date: datetime
    total_calls: int
    calls_answered_within_target: int
    service_level_percentage: float
    average_wait_time: float
    total_queue_time: int
    peak_wait_time: int
    queue_time_limit_breached: bool
    last_updated: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DashboardData(BaseModel):
    """Complete dashboard data model."""
    agents: List[AgentState]
    queues: List[QueueMetrics]
    service_level: ServiceLevelMetrics
    system_status: str = "operational"
    last_updated: datetime = Field(default_factory=datetime.now)
    alerts: List[str] = []


class AlertData(BaseModel):
    """Alert data model."""
    alert_id: str
    type: str  # "queue_warning", "queue_critical", "service_level"
    message: str
    severity: str  # "low", "medium", "high", "critical"
    timestamp: datetime = Field(default_factory=datetime.now)
    acknowledged: bool = False


class HistoricalData(BaseModel):
    """Historical data point model."""
    timestamp: datetime
    queue_id: str
    wait_time: int
    queue_depth: int
    service_level: float
    total_agents: int
    available_agents: int


# Admin Configuration Models

class MonitoredService(BaseModel):
    """Configuration for monitored services/queues."""
    id: Optional[int] = None
    trio_service_id: str
    service_name: str
    sla_target_seconds: int = 20
    warning_threshold_seconds: int = 15
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MonitoredUser(BaseModel):
    """Configuration for monitored users/agents."""
    id: Optional[int] = None
    trio_user_id: str
    user_name: str
    display_name: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TimeWindow(BaseModel):
    """Configuration for measurement time windows."""
    id: Optional[int] = None
    name: str  # "Vardagar" / "Helger"
    start_time: time
    end_time: time
    weekdays: List[int]  # 1=Monday, 7=Sunday
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            time: lambda v: v.isoformat()
        }


class SLAMetrics(BaseModel):
    """Historical SLA metrics within time windows."""
    id: Optional[int] = None
    service_id: int  # Foreign key to MonitoredService
    measurement_date: date
    time_window_id: int  # Foreign key to TimeWindow
    average_wait_time: float
    total_calls: int
    calls_within_sla: int
    sla_percentage: float
    peak_wait_time: Optional[int] = None
    created_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


# Theme Configuration Models

class ThemeType(str, Enum):
    """Theme types for the interface."""
    LIGHT = "light"
    DARK = "dark"


class ThemeSchedule(BaseModel):
    """Configuration for automatic theme switching."""
    id: Optional[int] = None
    name: str  # "Dagstema" / "Natttema"
    theme_type: ThemeType
    start_time: time
    end_time: time
    weekdays: List[int]  # 1=Monday, 7=Sunday
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            time: lambda v: v.isoformat()
        }


class ThemeSettings(BaseModel):
    """Custom theme color settings."""
    id: Optional[int] = None
    theme_type: ThemeType
    primary_color: str = "#1976d2"
    background_color: str = "#ffffff"
    surface_color: str = "#f5f5f5"
    text_primary: str = "#000000"
    text_secondary: str = "#666666"
    border_color: str = "#e0e0e0"
    success_color: str = "#4caf50"
    warning_color: str = "#ff9800"
    error_color: str = "#f44336"
    is_default: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# API Response Models

class TrioServiceInfo(BaseModel):
    """Information about available Trio services."""
    id: str
    name: str
    description: Optional[str] = None
    is_active: bool = True


class TrioUserInfo(BaseModel):
    """Information about available Trio users/agents."""
    id: str
    name: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    is_active: bool = True


class AdminConfigResponse(BaseModel):
    """Response model for admin configuration data."""
    monitored_services: List[MonitoredService]
    monitored_users: List[MonitoredUser]
    time_windows: List[TimeWindow]
    theme_schedule: List[ThemeSchedule]
    

class ThemeStatusResponse(BaseModel):
    """Current theme status response."""
    current_theme: ThemeType
    auto_theme_enabled: bool
    next_switch_time: Optional[datetime] = None
    manual_override: bool = False
