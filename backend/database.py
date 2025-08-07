"""Database module for Trio Monitor application."""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, Date, Time, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from config import settings

Base = declarative_base()


class AgentStateDB(Base):
    """Agent state database model."""
    __tablename__ = "agent_states"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, unique=True, index=True)
    name = Column(String)
    status = Column(String)
    current_call_duration = Column(Integer)
    calls_handled_today = Column(Integer, default=0)
    average_call_time = Column(Float)
    last_updated = Column(DateTime, default=datetime.now)


class QueueMetricsDB(Base):
    """Queue metrics database model."""
    __tablename__ = "queue_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    queue_id = Column(String, index=True)
    queue_name = Column(String)
    current_wait_time = Column(Integer)
    queue_depth = Column(Integer)
    status = Column(String)
    calls_waiting = Column(Integer)
    longest_wait_time = Column(Integer)
    average_wait_time = Column(Float)
    timestamp = Column(DateTime, default=datetime.now, index=True)


class ServiceLevelDB(Base):
    """Service level database model."""
    __tablename__ = "service_levels"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, index=True)
    total_calls = Column(Integer)
    calls_answered_within_target = Column(Integer)
    service_level_percentage = Column(Float)
    average_wait_time = Column(Float)
    total_queue_time = Column(Integer)
    peak_wait_time = Column(Integer)
    queue_time_limit_breached = Column(Boolean, default=False)


class AlertDB(Base):
    """Alert database model."""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String, unique=True, index=True)
    type = Column(String)
    message = Column(Text)
    severity = Column(String)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    acknowledged = Column(Boolean, default=False)


class HistoricalDataDB(Base):
    """Historical data database model."""
    __tablename__ = "historical_data"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True)
    queue_id = Column(String, index=True)
    wait_time = Column(Integer)
    queue_depth = Column(Integer)
    service_level = Column(Float)
    total_agents = Column(Integer)
    available_agents = Column(Integer)


# Admin Configuration Database Models

class MonitoredServiceDB(Base):
    """Monitored services database model."""
    __tablename__ = "monitored_services"
    
    id = Column(Integer, primary_key=True, index=True)
    trio_service_id = Column(String, unique=True, index=True)
    service_name = Column(String)
    sla_target_seconds = Column(Integer, default=20)
    warning_threshold_seconds = Column(Integer, default=15)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class MonitoredUserDB(Base):
    """Monitored users database model."""
    __tablename__ = "monitored_users"
    
    id = Column(Integer, primary_key=True, index=True)
    trio_user_id = Column(String, unique=True, index=True)
    user_name = Column(String)
    display_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class TimeWindowDB(Base):
    """Time windows database model."""
    __tablename__ = "time_windows"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)  # "Vardagar" / "Helger"
    start_time = Column(Time)
    end_time = Column(Time)
    weekdays = Column(JSON)  # [1,2,3,4,5] for Mon-Fri
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class SLAMetricsDB(Base):
    """SLA metrics database model."""
    __tablename__ = "sla_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("monitored_services.id"))
    measurement_date = Column(Date, index=True)
    time_window_id = Column(Integer, ForeignKey("time_windows.id"))
    average_wait_time = Column(Float)
    total_calls = Column(Integer)
    calls_within_sla = Column(Integer)
    sla_percentage = Column(Float)
    peak_wait_time = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    service = relationship("MonitoredServiceDB")
    time_window = relationship("TimeWindowDB")


class ThemeScheduleDB(Base):
    """Theme schedule database model."""
    __tablename__ = "theme_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)  # "Dagstema" / "Natttema"
    theme_type = Column(String)  # "light" / "dark"
    start_time = Column(Time)
    end_time = Column(Time)
    weekdays = Column(JSON)  # [1,2,3,4,5,6,7]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ThemeSettingsDB(Base):
    """Theme settings database model."""
    __tablename__ = "theme_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    theme_type = Column(String)  # "light" / "dark"
    primary_color = Column(String, default="#1976d2")
    background_color = Column(String, default="#ffffff")
    surface_color = Column(String, default="#f5f5f5")
    text_primary = Column(String, default="#000000")
    text_secondary = Column(String, default="#666666")
    border_color = Column(String, default="#e0e0e0")
    success_color = Column(String, default="#4caf50")
    warning_color = Column(String, default="#ff9800")
    error_color = Column(String, default="#f44336")
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# Database setup
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DatabaseManager:
    """Database manager for caching and historical data."""
    
    def __init__(self):
        create_tables()
    
    def cache_agent_states(self, db: Session, agents: List[dict]) -> None:
        """Cache agent states in database."""
        for agent_data in agents:
            agent = db.query(AgentStateDB).filter(
                AgentStateDB.agent_id == agent_data["agent_id"]
            ).first()
            
            if agent:
                # Update existing agent
                for key, value in agent_data.items():
                    setattr(agent, key, value)
                agent.last_updated = datetime.now()
            else:
                # Create new agent
                agent = AgentStateDB(**agent_data)
                db.add(agent)
        
        db.commit()
    
    def cache_queue_metrics(self, db: Session, queues: List[dict]) -> None:
        """Cache queue metrics in database."""
        for queue_data in queues:
            queue_metric = QueueMetricsDB(**queue_data)
            db.add(queue_metric)
        
        db.commit()
    
    def get_cached_data(self, db: Session, max_age_seconds: int = 300) -> Optional[dict]:
        """Get cached data if within max age."""
        cutoff_time = datetime.now() - timedelta(seconds=max_age_seconds)
        
        # Get latest agent states
        agents = db.query(AgentStateDB).filter(
            AgentStateDB.last_updated > cutoff_time
        ).all()
        
        # Get latest queue metrics
        queues = db.query(QueueMetricsDB).filter(
            QueueMetricsDB.timestamp > cutoff_time
        ).all()
        
        if not agents and not queues:
            return None
        
        return {
            "agents": [self._agent_to_dict(agent) for agent in agents],
            "queues": [self._queue_to_dict(queue) for queue in queues],
            "cached_at": datetime.now()
        }
    
    def store_historical_data(self, db: Session, data: dict) -> None:
        """Store historical data point."""
        historical = HistoricalDataDB(**data)
        db.add(historical)
        db.commit()
    
    def cleanup_old_data(self, db: Session, days_to_keep: int = 30) -> None:
        """Clean up old historical data."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        db.query(QueueMetricsDB).filter(
            QueueMetricsDB.timestamp < cutoff_date
        ).delete()
        
        db.query(HistoricalDataDB).filter(
            HistoricalDataDB.timestamp < cutoff_date
        ).delete()
        
        db.commit()
    
    def _agent_to_dict(self, agent: AgentStateDB) -> dict:
        """Convert agent DB model to dictionary."""
        return {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "status": agent.status,
            "current_call_duration": agent.current_call_duration,
            "calls_handled_today": agent.calls_handled_today,
            "average_call_time": agent.average_call_time,
            "last_updated": agent.last_updated
        }
    
    def _queue_to_dict(self, queue: QueueMetricsDB) -> dict:
        """Convert queue DB model to dictionary."""
        return {
            "queue_id": queue.queue_id,
            "queue_name": queue.queue_name,
            "current_wait_time": queue.current_wait_time,
            "queue_depth": queue.queue_depth,
            "status": queue.status,
            "calls_waiting": queue.calls_waiting,
            "longest_wait_time": queue.longest_wait_time,
            "average_wait_time": queue.average_wait_time,
            "last_updated": queue.timestamp
        }


# Global database manager instance
db_manager = DatabaseManager()
