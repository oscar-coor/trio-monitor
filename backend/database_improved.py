"""Improved database module with better session management and async support."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Generator
from contextlib import contextmanager
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.pool import NullPool
import logging

from config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


class AgentStateDB(Base):
    """Agent state database model with indexes."""
    __tablename__ = "agent_states"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, index=True)
    current_call_duration = Column(Integer, nullable=True)
    calls_handled_today = Column(Integer, default=0, nullable=False)
    average_call_time = Column(Float, nullable=True)
    last_updated = Column(DateTime, default=datetime.now, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_agent_status_updated', 'status', 'last_updated'),
    )


class QueueMetricsDB(Base):
    """Queue metrics database model with composite indexes."""
    __tablename__ = "queue_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    queue_id = Column(String(50), nullable=False, index=True)
    queue_name = Column(String(100), nullable=False)
    current_wait_time = Column(Integer, nullable=False)
    queue_depth = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, index=True)
    calls_waiting = Column(Integer, nullable=False)
    longest_wait_time = Column(Integer, nullable=False)
    average_wait_time = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.now, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_queue_timestamp', 'queue_id', 'timestamp'),
        Index('idx_queue_status_time', 'status', 'timestamp'),
    )


class ServiceLevelDB(Base):
    """Service level database model."""
    __tablename__ = "service_levels"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    total_calls = Column(Integer, nullable=False)
    calls_answered_within_target = Column(Integer, nullable=False)
    service_level_percentage = Column(Float, nullable=False)
    average_wait_time = Column(Float, nullable=False)
    total_queue_time = Column(Integer, nullable=False)
    peak_wait_time = Column(Integer, nullable=False)
    queue_time_limit_breached = Column(Boolean, default=False, nullable=False)


class AlertDB(Base):
    """Alert database model with better indexing."""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(100), unique=True, nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)
    message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.now, nullable=False, index=True)
    acknowledged = Column(Boolean, default=False, nullable=False, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(100), nullable=True)
    
    __table_args__ = (
        Index('idx_alert_unack', 'acknowledged', 'severity', 'timestamp'),
    )


class HistoricalDataDB(Base):
    """Historical data database model with partitioning support."""
    __tablename__ = "historical_data"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    queue_id = Column(String(50), nullable=False, index=True)
    wait_time = Column(Integer, nullable=False)
    queue_depth = Column(Integer, nullable=False)
    service_level = Column(Float, nullable=False)
    total_agents = Column(Integer, nullable=False)
    available_agents = Column(Integer, nullable=False)
    
    __table_args__ = (
        Index('idx_historical_queue_time', 'queue_id', 'timestamp'),
    )


# Database configuration with connection pooling
def get_engine():
    """Create database engine with proper pooling for SQLite."""
    if "sqlite" in settings.database_url:
        # SQLite doesn't support connection pooling well
        return create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False, "timeout": 30},
            poolclass=NullPool,  # No connection pooling for SQLite
            echo=settings.debug
        )
    else:
        # For PostgreSQL/MySQL use connection pooling
        return create_engine(
            settings.database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before using
            echo=settings.debug
        )


# Create engine and session factory
engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables with error handling."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for database sessions with proper cleanup."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """Get database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ImprovedDatabaseManager:
    """Enhanced database manager with better error handling and transactions."""
    
    def __init__(self):
        """Initialize database manager and ensure tables exist."""
        try:
            create_tables()
            logger.info("Database manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def cache_agent_states(self, db: Session, agents: List[Dict[str, Any]]) -> None:
        """Cache agent states with upsert logic and error handling."""
        try:
            for agent_data in agents:
                # Validate required fields
                if not agent_data.get("agent_id"):
                    logger.warning(f"Skipping agent with missing ID: {agent_data}")
                    continue
                
                agent = db.query(AgentStateDB).filter(
                    AgentStateDB.agent_id == agent_data["agent_id"]
                ).first()
                
                if agent:
                    # Update existing agent
                    for key, value in agent_data.items():
                        if hasattr(agent, key):
                            setattr(agent, key, value)
                    agent.last_updated = datetime.now()
                else:
                    # Create new agent
                    agent_data["last_updated"] = datetime.now()
                    agent = AgentStateDB(**agent_data)
                    db.add(agent)
            
            db.flush()  # Flush but don't commit yet
            logger.debug(f"Cached {len(agents)} agent states")
            
        except IntegrityError as e:
            logger.error(f"Integrity error caching agents: {e}")
            db.rollback()
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error caching agents: {e}")
            db.rollback()
            raise
    
    def cache_queue_metrics(self, db: Session, queues: List[Dict[str, Any]]) -> None:
        """Cache queue metrics with validation."""
        try:
            for queue_data in queues:
                # Validate required fields
                if not queue_data.get("queue_id"):
                    logger.warning(f"Skipping queue with missing ID: {queue_data}")
                    continue
                
                # Ensure timestamp
                if "timestamp" not in queue_data:
                    queue_data["timestamp"] = datetime.now()
                
                queue_metric = QueueMetricsDB(**queue_data)
                db.add(queue_metric)
            
            db.flush()
            logger.debug(f"Cached {len(queues)} queue metrics")
            
        except SQLAlchemyError as e:
            logger.error(f"Database error caching queues: {e}")
            db.rollback()
            raise
    
    def get_cached_data(self, db: Session, max_age_seconds: int = 300) -> Optional[Dict[str, Any]]:
        """Get cached data with age validation."""
        try:
            cutoff_time = datetime.now() - timedelta(seconds=max_age_seconds)
            
            # Get latest agent states
            agents = db.query(AgentStateDB).filter(
                AgentStateDB.last_updated > cutoff_time
            ).all()
            
            # Get latest queue metrics (limit to prevent memory issues)
            queues = db.query(QueueMetricsDB).filter(
                QueueMetricsDB.timestamp > cutoff_time
            ).order_by(QueueMetricsDB.timestamp.desc()).limit(100).all()
            
            if not agents and not queues:
                return None
            
            return {
                "agents": [self._agent_to_dict(agent) for agent in agents],
                "queues": [self._queue_to_dict(queue) for queue in queues],
                "cached_at": datetime.now(),
                "is_stale": False
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving cached data: {e}")
            return None
    
    def store_historical_data(self, db: Session, data: Dict[str, Any]) -> None:
        """Store historical data with validation."""
        try:
            # Validate required fields
            required_fields = ["queue_id", "wait_time", "queue_depth", "service_level"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add timestamp if not present
            if "timestamp" not in data:
                data["timestamp"] = datetime.now()
            
            historical = HistoricalDataDB(**data)
            db.add(historical)
            db.flush()
            
        except (ValueError, SQLAlchemyError) as e:
            logger.error(f"Error storing historical data: {e}")
            db.rollback()
            raise
    
    def cleanup_old_data(self, db: Session, days_to_keep: int = 30) -> int:
        """Clean up old data and return count of deleted records."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            # Delete old queue metrics
            deleted_queues = db.query(QueueMetricsDB).filter(
                QueueMetricsDB.timestamp < cutoff_date
            ).delete()
            deleted_count += deleted_queues
            
            # Delete old historical data
            deleted_historical = db.query(HistoricalDataDB).filter(
                HistoricalDataDB.timestamp < cutoff_date
            ).delete()
            deleted_count += deleted_historical
            
            # Delete old acknowledged alerts
            week_ago = datetime.now() - timedelta(days=7)
            deleted_alerts = db.query(AlertDB).filter(
                AlertDB.acknowledged == True,
                AlertDB.acknowledged_at < week_ago
            ).delete()
            deleted_count += deleted_alerts
            
            db.commit()
            logger.info(f"Cleaned up {deleted_count} old records")
            return deleted_count
            
        except SQLAlchemyError as e:
            logger.error(f"Error cleaning up old data: {e}")
            db.rollback()
            raise
    
    def get_queue_statistics(self, db: Session, queue_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get detailed statistics for a queue."""
        try:
            start_time = datetime.now() - timedelta(hours=hours)
            
            metrics = db.query(QueueMetricsDB).filter(
                QueueMetricsDB.queue_id == queue_id,
                QueueMetricsDB.timestamp >= start_time
            ).all()
            
            if not metrics:
                return {}
            
            wait_times = [m.current_wait_time for m in metrics]
            
            return {
                "queue_id": queue_id,
                "period_hours": hours,
                "data_points": len(metrics),
                "avg_wait_time": sum(wait_times) / len(wait_times),
                "max_wait_time": max(wait_times),
                "min_wait_time": min(wait_times),
                "critical_count": sum(1 for m in metrics if m.status == "critical"),
                "warning_count": sum(1 for m in metrics if m.status == "warning"),
                "good_count": sum(1 for m in metrics if m.status == "good")
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting queue statistics: {e}")
            return {}
    
    def _agent_to_dict(self, agent: AgentStateDB) -> Dict[str, Any]:
        """Convert agent DB model to dictionary safely."""
        return {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "status": agent.status,
            "current_call_duration": agent.current_call_duration,
            "calls_handled_today": agent.calls_handled_today,
            "average_call_time": agent.average_call_time,
            "last_updated": agent.last_updated.isoformat() if agent.last_updated else None
        }
    
    def _queue_to_dict(self, queue: QueueMetricsDB) -> Dict[str, Any]:
        """Convert queue DB model to dictionary safely."""
        return {
            "queue_id": queue.queue_id,
            "queue_name": queue.queue_name,
            "current_wait_time": queue.current_wait_time,
            "queue_depth": queue.queue_depth,
            "status": queue.status,
            "calls_waiting": queue.calls_waiting,
            "longest_wait_time": queue.longest_wait_time,
            "average_wait_time": queue.average_wait_time,
            "last_updated": queue.timestamp.isoformat() if queue.timestamp else None
        }


# Global database manager instance
db_manager = ImprovedDatabaseManager()
