"""Data models for Trio Monitor application."""

from datetime import date, datetime, time
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
    current_call_duration: int | None = None
    calls_handled_today: int = 0
    average_call_time: float | None = None
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
    last_updated: datetime | None = None



class DashboardData(BaseModel):
    """Complete dashboard data model."""
    agents: list[AgentState]
    queues: list[QueueMetrics]
    service_level: ServiceLevelMetrics
    system_status: str = "operational"
    last_updated: datetime = Field(default_factory=datetime.now)
    alerts: list[str] = []


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
    id: int | None = None
    trio_service_id: str
    service_name: str
    sla_target_seconds: int = 20
    warning_threshold_seconds: int = 15
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None



class MonitoredUser(BaseModel):
    """Configuration for monitored users/agents."""
    id: int | None = None
    trio_user_id: str
    user_name: str
    display_name: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None



class TimeWindow(BaseModel):
    """Configuration for measurement time windows."""
    id: int | None = None
    name: str  # "Vardagar" / "Helger"
    start_time: time
    end_time: time
    weekdays: list[int]  # 1=Monday, 7=Sunday
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None



class SLAMetrics(BaseModel):
    """Historical SLA metrics within time windows."""
    id: int | None = None
    service_id: int  # Foreign key to MonitoredService
    measurement_date: date
    time_window_id: int  # Foreign key to TimeWindow
    average_wait_time: float
    total_calls: int
    calls_within_sla: int
    sla_percentage: float
    peak_wait_time: int | None = None
    created_at: datetime | None = None



# Theme Configuration Models

class ThemeType(str, Enum):
    """Theme types for the interface."""
    LIGHT = "light"
    DARK = "dark"


class ThemeSchedule(BaseModel):
    """Configuration for automatic theme switching."""
    id: int | None = None
    name: str  # "Dagstema" / "Natttema"
    theme_type: ThemeType
    start_time: time
    end_time: time
    weekdays: list[int]  # 1=Monday, 7=Sunday
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None



class ThemeSettings(BaseModel):
    """Custom theme color settings."""
    id: int | None = None
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
    created_at: datetime | None = None
    updated_at: datetime | None = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# API Response Models

class TrioServiceInfo(BaseModel):
    """Information about available Trio services."""
    id: str
    name: str
    description: str | None = None
    is_active: bool = True


class TrioUserInfo(BaseModel):
    """Information about available Trio users/agents."""
    id: str
    name: str
    display_name: str | None = None
    email: str | None = None
    is_active: bool = True


class AdminConfigResponse(BaseModel):
    """Response model for admin configuration data."""
    monitored_services: list[MonitoredService]
    monitored_users: list[MonitoredUser]
    time_windows: list[TimeWindow]
    theme_schedule: list[ThemeSchedule]
    

class ThemeStatusResponse(BaseModel):
    """Current theme status response."""
    current_theme: ThemeType
    auto_theme_enabled: bool
    next_switch_time: datetime | None = None
    manual_override: bool = False


# Connection settings (admin-manageable)
class ConnectionSettings(BaseModel):
    """Configuration for Trio server connection and credentials."""
    base_url: str
    username: str | None = None
    password: str | None = None  # write-only; do not log
    api_token: str | None = None
    contact_center_id: str = "1"
    has_token: bool = False  # indicates a stored token exists server-side
