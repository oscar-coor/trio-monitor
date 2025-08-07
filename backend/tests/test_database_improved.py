"""Tests for improved database module."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_improved import (
    ImprovedDatabaseManager, 
    AgentStateDB, 
    QueueMetricsDB,
    ServiceLevelDB,
    AlertDB,
    HistoricalDataDB,
    get_db_context,
    create_tables
)


class TestImprovedDatabaseManager:
    """Test suite for ImprovedDatabaseManager."""
    
    @pytest.fixture
    def db_manager(self):
        """Create a database manager instance."""
        with patch('database_improved.create_tables'):
            return ImprovedDatabaseManager()
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = MagicMock(spec=Session)
        session.query.return_value.filter.return_value.first.return_value = None
        return session
    
    def test_database_manager_initialization(self):
        """Test database manager initializes and creates tables."""
        with patch('database_improved.create_tables') as mock_create:
            manager = ImprovedDatabaseManager()
            mock_create.assert_called_once()
    
    def test_cache_agent_states_new_agent(self, db_manager, mock_session):
        """Test caching new agent states."""
        agents = [
            {
                "agent_id": "agent1",
                "name": "Test Agent",
                "status": "available",
                "current_call_duration": 0,
                "calls_handled_today": 5,
                "average_call_time": 180.0
            }
        ]
        
        # Mock query to return no existing agent
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        db_manager.cache_agent_states(mock_session, agents)
        
        # Should add new agent
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
    
    def test_cache_agent_states_update_existing(self, db_manager, mock_session):
        """Test updating existing agent states."""
        agents = [
            {
                "agent_id": "agent1",
                "name": "Test Agent",
                "status": "busy",
                "current_call_duration": 120,
                "calls_handled_today": 6,
                "average_call_time": 190.0
            }
        ]
        
        # Mock existing agent
        mock_agent = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_agent
        
        db_manager.cache_agent_states(mock_session, agents)
        
        # Should update existing agent
        assert mock_agent.status == "busy"
        assert mock_agent.current_call_duration == 120
        assert mock_agent.calls_handled_today == 6
        mock_session.flush.assert_called_once()
    
    def test_cache_agent_states_skip_invalid(self, db_manager, mock_session):
        """Test skipping agents with missing ID."""
        agents = [
            {"name": "No ID Agent", "status": "available"},  # Missing agent_id
            {
                "agent_id": "agent2",
                "name": "Valid Agent",
                "status": "available"
            }
        ]
        
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        db_manager.cache_agent_states(mock_session, agents)
        
        # Should only add one agent (the valid one)
        assert mock_session.add.call_count == 1
    
    def test_cache_agent_states_integrity_error(self, db_manager, mock_session):
        """Test handling integrity errors when caching agents."""
        agents = [{"agent_id": "agent1", "name": "Test Agent", "status": "available"}]
        
        mock_session.flush.side_effect = IntegrityError("", "", "")
        
        with pytest.raises(IntegrityError):
            db_manager.cache_agent_states(mock_session, agents)
        
        mock_session.rollback.assert_called_once()
    
    def test_cache_queue_metrics_success(self, db_manager, mock_session):
        """Test caching queue metrics successfully."""
        queues = [
            {
                "queue_id": "q1",
                "queue_name": "Kundtjänst",
                "current_wait_time": 15,
                "queue_depth": 3,
                "status": "warning",
                "calls_waiting": 2,
                "longest_wait_time": 20,
                "average_wait_time": 12.5
            }
        ]
        
        db_manager.cache_queue_metrics(mock_session, queues)
        
        # Should add queue metric
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        
        # Check timestamp was added
        call_args = mock_session.add.call_args[0][0]
        assert hasattr(call_args, 'timestamp')
    
    def test_cache_queue_metrics_skip_invalid(self, db_manager, mock_session):
        """Test skipping queues with missing ID."""
        queues = [
            {"queue_name": "No ID Queue"},  # Missing queue_id
            {
                "queue_id": "q2",
                "queue_name": "Valid Queue",
                "current_wait_time": 10
            }
        ]
        
        db_manager.cache_queue_metrics(mock_session, queues)
        
        # Should only add one queue (the valid one)
        assert mock_session.add.call_count == 1
    
    def test_get_cached_data_success(self, db_manager, mock_session):
        """Test retrieving cached data successfully."""
        # Mock agent data
        mock_agent = MagicMock()
        mock_agent.agent_id = "agent1"
        mock_agent.name = "Test Agent"
        mock_agent.status = "available"
        mock_agent.current_call_duration = 0
        mock_agent.calls_handled_today = 5
        mock_agent.average_call_time = 180.0
        mock_agent.last_updated = datetime.now()
        
        # Mock queue data
        mock_queue = MagicMock()
        mock_queue.queue_id = "q1"
        mock_queue.queue_name = "Kundtjänst"
        mock_queue.current_wait_time = 15
        mock_queue.queue_depth = 3
        mock_queue.status = "warning"
        mock_queue.calls_waiting = 2
        mock_queue.longest_wait_time = 20
        mock_queue.average_wait_time = 12.5
        mock_queue.timestamp = datetime.now()
        
        mock_session.query.return_value.filter.return_value.all.return_value = [mock_agent]
        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_queue]
        
        result = db_manager.get_cached_data(mock_session, max_age_seconds=300)
        
        assert result is not None
        assert len(result["agents"]) == 1
        assert len(result["queues"]) == 1
        assert result["is_stale"] == False
        assert "cached_at" in result
    
    def test_get_cached_data_no_data(self, db_manager, mock_session):
        """Test retrieving cached data when none exists."""
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        result = db_manager.get_cached_data(mock_session, max_age_seconds=300)
        
        assert result is None
    
    def test_get_cached_data_error_handling(self, db_manager, mock_session):
        """Test error handling when retrieving cached data."""
        mock_session.query.side_effect = SQLAlchemyError("Database error")
        
        result = db_manager.get_cached_data(mock_session)
        
        assert result is None
    
    def test_store_historical_data_success(self, db_manager, mock_session):
        """Test storing historical data successfully."""
        data = {
            "queue_id": "q1",
            "wait_time": 15,
            "queue_depth": 3,
            "service_level": 85.0,
            "total_agents": 10,
            "available_agents": 3
        }
        
        db_manager.store_historical_data(mock_session, data)
        
        # Should add historical record
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        
        # Check timestamp was added
        call_args = mock_session.add.call_args[0][0]
        assert hasattr(call_args, 'timestamp')
    
    def test_store_historical_data_missing_fields(self, db_manager, mock_session):
        """Test storing historical data with missing required fields."""
        data = {
            "queue_id": "q1",
            "wait_time": 15
            # Missing queue_depth and service_level
        }
        
        with pytest.raises(ValueError) as exc_info:
            db_manager.store_historical_data(mock_session, data)
        
        assert "Missing required field" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
    
    def test_cleanup_old_data_success(self, db_manager, mock_session):
        """Test cleaning up old data successfully."""
        # Mock delete operations
        mock_session.query.return_value.filter.return_value.delete.return_value = 100
        
        deleted_count = db_manager.cleanup_old_data(mock_session, days_to_keep=30)
        
        # Should delete from 3 tables (queues, historical, alerts)
        assert mock_session.query.call_count == 3
        assert deleted_count == 300  # 100 from each table
        mock_session.commit.assert_called_once()
    
    def test_cleanup_old_data_error_handling(self, db_manager, mock_session):
        """Test error handling during cleanup."""
        mock_session.query.return_value.filter.return_value.delete.side_effect = SQLAlchemyError("Delete error")
        
        with pytest.raises(SQLAlchemyError):
            db_manager.cleanup_old_data(mock_session)
        
        mock_session.rollback.assert_called_once()
    
    def test_get_queue_statistics_success(self, db_manager, mock_session):
        """Test getting queue statistics successfully."""
        # Mock queue metrics
        mock_metrics = []
        for i in range(10):
            metric = MagicMock()
            metric.current_wait_time = 10 + i
            metric.status = "good" if i < 5 else "warning"
            mock_metrics.append(metric)
        
        mock_session.query.return_value.filter.return_value.all.return_value = mock_metrics
        
        stats = db_manager.get_queue_statistics(mock_session, "q1", hours=24)
        
        assert stats["queue_id"] == "q1"
        assert stats["period_hours"] == 24
        assert stats["data_points"] == 10
        assert stats["avg_wait_time"] == 14.5  # Average of 10-19
        assert stats["max_wait_time"] == 19
        assert stats["min_wait_time"] == 10
        assert stats["good_count"] == 5
        assert stats["warning_count"] == 5
        assert stats["critical_count"] == 0
    
    def test_get_queue_statistics_no_data(self, db_manager, mock_session):
        """Test getting queue statistics with no data."""
        mock_session.query.return_value.filter.return_value.all.return_value = []
        
        stats = db_manager.get_queue_statistics(mock_session, "q1", hours=24)
        
        assert stats == {}
    
    def test_get_queue_statistics_error_handling(self, db_manager, mock_session):
        """Test error handling when getting queue statistics."""
        mock_session.query.side_effect = SQLAlchemyError("Query error")
        
        stats = db_manager.get_queue_statistics(mock_session, "q1", hours=24)
        
        assert stats == {}
    
    def test_agent_to_dict_conversion(self, db_manager):
        """Test converting agent DB model to dictionary."""
        mock_agent = MagicMock(spec=AgentStateDB)
        mock_agent.agent_id = "agent1"
        mock_agent.name = "Test Agent"
        mock_agent.status = "available"
        mock_agent.current_call_duration = 0
        mock_agent.calls_handled_today = 5
        mock_agent.average_call_time = 180.0
        mock_agent.last_updated = datetime.now()
        
        result = db_manager._agent_to_dict(mock_agent)
        
        assert result["agent_id"] == "agent1"
        assert result["name"] == "Test Agent"
        assert result["status"] == "available"
        assert result["current_call_duration"] == 0
        assert result["calls_handled_today"] == 5
        assert result["average_call_time"] == 180.0
        assert "last_updated" in result
    
    def test_queue_to_dict_conversion(self, db_manager):
        """Test converting queue DB model to dictionary."""
        mock_queue = MagicMock(spec=QueueMetricsDB)
        mock_queue.queue_id = "q1"
        mock_queue.queue_name = "Kundtjänst"
        mock_queue.current_wait_time = 15
        mock_queue.queue_depth = 3
        mock_queue.status = "warning"
        mock_queue.calls_waiting = 2
        mock_queue.longest_wait_time = 20
        mock_queue.average_wait_time = 12.5
        mock_queue.timestamp = datetime.now()
        
        result = db_manager._queue_to_dict(mock_queue)
        
        assert result["queue_id"] == "q1"
        assert result["queue_name"] == "Kundtjänst"
        assert result["current_wait_time"] == 15
        assert result["queue_depth"] == 3
        assert result["status"] == "warning"
        assert result["calls_waiting"] == 2
        assert result["longest_wait_time"] == 20
        assert result["average_wait_time"] == 12.5
        assert "last_updated" in result


@pytest.mark.integration
class TestDatabaseIntegration:
    """Integration tests for database operations."""
    
    @pytest.fixture
    def test_db(self):
        """Create a test database."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from database_improved import Base
        
        # Use in-memory SQLite for tests
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        
        db = SessionLocal()
        yield db
        db.close()
    
    def test_end_to_end_agent_caching(self, test_db):
        """Test end-to-end agent caching and retrieval."""
        manager = ImprovedDatabaseManager()
        
        # Cache agents
        agents = [
            {
                "agent_id": "agent1",
                "name": "Test Agent 1",
                "status": "available",
                "current_call_duration": 0,
                "calls_handled_today": 5,
                "average_call_time": 180.0
            }
        ]
        
        manager.cache_agent_states(test_db, agents)
        test_db.commit()
        
        # Retrieve cached data
        cached = manager.get_cached_data(test_db, max_age_seconds=300)
        
        assert cached is not None
        assert len(cached["agents"]) == 1
        assert cached["agents"][0]["agent_id"] == "agent1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
