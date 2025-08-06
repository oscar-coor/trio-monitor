"""Data models for Trio Monitor application."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


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
    """Service level metrics model."""
    date: datetime
    total_calls: int
    calls_answered_within_target: int
    service_level_percentage: float
    average_wait_time: float
    total_queue_time: int  # Total accumulated queue time in seconds
    peak_wait_time: int
    queue_time_limit_breached: bool = False


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
