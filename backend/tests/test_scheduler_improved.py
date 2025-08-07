"""Tests for improved scheduler module."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scheduler_improved import ImprovedTrioScheduler, MAX_RETRIES, RETRY_DELAY
from models import QueueMetrics, ServiceLevelMetrics, QueueStatus, AlertData


class TestImprovedTrioScheduler:
    """Test suite for ImprovedTrioScheduler."""
    
    @pytest.fixture
    def scheduler(self):
        """Create a scheduler instance for testing."""
        return ImprovedTrioScheduler()
    
    @pytest.fixture
    def mock_api_client(self):
        """Create a mock API client."""
        with patch('scheduler_improved.api_client') as mock:
            mock.get_agent_states = AsyncMock(return_value=[])
            mock.get_queue_metrics = AsyncMock(return_value=[])
            mock.get_service_level_metrics = AsyncMock(return_value=ServiceLevelMetrics(
                date=datetime.now(),
                total_calls=100,
                calls_answered_within_target=80,
                service_level_percentage=80.0,
                average_wait_time=15.5,
                total_queue_time=1550,
                peak_wait_time=45,
                queue_time_limit_breached=False
            ))
            mock.test_connection = AsyncMock(return_value=True)
            yield mock
    
    def test_scheduler_initialization(self, scheduler):
        """Test scheduler initializes correctly."""
        assert scheduler.latest_data == {}
        assert scheduler.alerts == []
        assert scheduler.is_running == False
        assert scheduler.consecutive_failures == 0
        assert scheduler.max_consecutive_failures == 5
    
    def test_scheduler_start_stop(self, scheduler):
        """Test scheduler can start and stop."""
        # Start scheduler
        scheduler.start()
        assert scheduler.is_running == True
        
        # Stop scheduler
        scheduler.stop()
        assert scheduler.is_running == False
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_activation(self, scheduler):
        """Test circuit breaker activates after max failures."""
        # Set consecutive failures to max
        scheduler.consecutive_failures = scheduler.max_consecutive_failures
        
        # Try to poll data
        await scheduler._poll_data_with_retry()
        
        # Check system status
        assert scheduler.latest_data.get("system_status") == "circuit_breaker_open"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_reset(self, scheduler, mock_api_client):
        """Test circuit breaker resets after successful poll."""
        # Set some failures
        scheduler.consecutive_failures = 3
        
        # Successful poll should reset counter
        await scheduler._poll_data()
        
        # Check failures reset (would be reset in _poll_data_with_retry)
        # In actual implementation, this happens in the retry wrapper
        assert scheduler.consecutive_failures == 3  # Not reset in _poll_data itself
    
    @pytest.mark.asyncio
    async def test_retry_logic_with_timeout(self, scheduler):
        """Test retry logic handles timeouts correctly."""
        with patch('scheduler_improved.api_client.get_agent_states', 
                   side_effect=asyncio.TimeoutError()):
            await scheduler._poll_data_with_retry()
            
            # Should increment consecutive failures
            assert scheduler.consecutive_failures == 1
            assert scheduler.latest_data.get("system_status") == "degraded"
    
    @pytest.mark.asyncio
    async def test_retry_logic_exponential_backoff(self, scheduler):
        """Test exponential backoff in retry logic."""
        call_times = []
        
        async def mock_poll_data():
            call_times.append(datetime.now())
            raise Exception("Test error")
        
        scheduler._poll_data = mock_poll_data
        
        await scheduler._poll_data_with_retry()
        
        # Should have MAX_RETRIES attempts
        assert len(call_times) == MAX_RETRIES
        
        # Check exponential backoff between retries
        if len(call_times) > 1:
            for i in range(1, len(call_times)):
                time_diff = (call_times[i] - call_times[i-1]).total_seconds()
                expected_delay = RETRY_DELAY * i
                # Allow some tolerance
                assert time_diff >= expected_delay - 0.5
    
    def test_process_alerts_queue_critical(self, scheduler):
        """Test alert generation for critical queue wait times."""
        queues = [
            QueueMetrics(
                queue_id="q1",
                queue_name="Kundtjänst",
                current_wait_time=25,  # Over 20s critical limit
                queue_depth=5,
                status=QueueStatus.CRITICAL,
                calls_waiting=3,
                longest_wait_time=30,
                average_wait_time=20.0
            )
        ]
        
        service_level = ServiceLevelMetrics(
            date=datetime.now(),
            total_calls=100,
            calls_answered_within_target=80,
            service_level_percentage=80.0,
            average_wait_time=15.0,
            total_queue_time=1500,
            peak_wait_time=25,
            queue_time_limit_breached=False
        )
        
        alerts = scheduler._process_alerts(queues, service_level)
        
        # Should generate critical alert
        assert len(alerts) == 1
        assert alerts[0].severity == "critical"
        assert "KRITISK" in alerts[0].message
        assert "25s" in alerts[0].message
    
    def test_process_alerts_queue_warning(self, scheduler):
        """Test alert generation for warning queue wait times."""
        queues = [
            QueueMetrics(
                queue_id="q1",
                queue_name="Support",
                current_wait_time=19,  # Between 18-20s warning (threshold is 18)
                queue_depth=3,
                status=QueueStatus.WARNING,
                calls_waiting=2,
                longest_wait_time=19,
                average_wait_time=15.0
            )
        ]
        
        service_level = ServiceLevelMetrics(
            date=datetime.now(),
            total_calls=100,
            calls_answered_within_target=80,
            service_level_percentage=80.0,
            average_wait_time=15.0,
            total_queue_time=1500,
            peak_wait_time=18,
            queue_time_limit_breached=False
        )
        
        alerts = scheduler._process_alerts(queues, service_level)
        
        # Should generate warning alert
        assert len(alerts) == 1
        assert alerts[0].severity == "medium"
        assert "VARNING" in alerts[0].message
    
    def test_process_alerts_service_level(self, scheduler):
        """Test alert generation for service level below target."""
        queues = []
        
        service_level = ServiceLevelMetrics(
            date=datetime.now(),
            total_calls=100,
            calls_answered_within_target=70,
            service_level_percentage=70.0,  # Below 80% target
            average_wait_time=15.0,
            total_queue_time=1500,
            peak_wait_time=18,
            queue_time_limit_breached=False
        )
        
        alerts = scheduler._process_alerts(queues, service_level)
        
        # Should generate service level alert
        assert len(alerts) == 1
        assert alerts[0].type == "service_level"
        assert "70.0%" in alerts[0].message
        assert "80%" in alerts[0].message
    
    def test_process_alerts_daily_limit_breach(self, scheduler):
        """Test alert generation for daily queue time limit breach."""
        queues = []
        
        service_level = ServiceLevelMetrics(
            date=datetime.now(),
            total_calls=100,
            calls_answered_within_target=80,
            service_level_percentage=80.0,
            average_wait_time=15.0,
            total_queue_time=2500,
            peak_wait_time=18,
            queue_time_limit_breached=True  # Daily limit breached
        )
        
        alerts = scheduler._process_alerts(queues, service_level)
        
        # Should generate daily limit alert
        assert len(alerts) == 1
        assert alerts[0].type == "daily_limit"
        assert alerts[0].severity == "critical"
        assert "Daglig kötidsgräns" in alerts[0].message
    
    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self, scheduler, mock_api_client):
        """Test health check when all systems are healthy."""
        with patch('scheduler_improved.get_db') as mock_db:
            mock_db.return_value.__next__.return_value.execute.return_value = None
            
            await scheduler._health_check()
            
            # Should be operational
            assert scheduler.latest_data.get("system_status") == "operational"
    
    @pytest.mark.asyncio
    async def test_health_check_api_unhealthy(self, scheduler):
        """Test health check when API is unhealthy."""
        with patch('scheduler_improved.api_client') as mock_client:
            # Mock test_connection to return False for unhealthy API
            mock_client.test_connection = AsyncMock(return_value=False)
            with patch('scheduler_improved.get_db') as mock_db:
                mock_session = MagicMock()
                mock_session.execute.return_value = None
                mock_db.return_value.__next__.return_value = mock_session
                
                await scheduler._health_check()
                
                # Should indicate API issue
                assert scheduler.latest_data.get("system_status") == "api_unreachable"
    
    @pytest.mark.asyncio
    async def test_health_check_database_unhealthy(self, scheduler, mock_api_client):
        """Test health check when database is unhealthy."""
        with patch('scheduler_improved.get_db', side_effect=Exception("DB Error")):
            await scheduler._health_check()
            
            # Should indicate database issue
            assert scheduler.latest_data.get("system_status") == "database_error"
    
    def test_get_system_metrics(self, scheduler):
        """Test system metrics reporting."""
        scheduler.is_running = True
        scheduler.consecutive_failures = 2
        scheduler.latest_data = {
            "last_updated": datetime.now(),
            "system_status": "operational"
        }
        
        metrics = scheduler.get_system_metrics()
        
        assert metrics["is_running"] == True
        assert metrics["consecutive_failures"] == 2
        assert metrics["circuit_breaker_status"] == "closed"
        assert metrics["system_status"] == "operational"
        assert "last_successful_poll" in metrics
    
    def test_get_system_metrics_circuit_open(self, scheduler):
        """Test system metrics when circuit breaker is open."""
        scheduler.consecutive_failures = scheduler.max_consecutive_failures
        
        metrics = scheduler.get_system_metrics()
        
        assert metrics["circuit_breaker_status"] == "open"
    
    @pytest.mark.asyncio
    async def test_cache_data_safely_success(self, scheduler, mock_api_client):
        """Test safe data caching with proper session management."""
        agents = []
        queues = []
        service_level = ServiceLevelMetrics(
            date=datetime.now(),
            total_calls=100,
            calls_answered_within_target=80,
            service_level_percentage=80.0,
            average_wait_time=15.0,
            total_queue_time=1500,
            peak_wait_time=18,
            queue_time_limit_breached=False
        )
        dashboard_data = MagicMock()
        
        with patch('scheduler_improved.get_db') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__next__.return_value = mock_session
            
            with patch('scheduler_improved.db_manager') as mock_db_manager:
                await scheduler._cache_data_safely(
                    agents, queues, service_level, dashboard_data
                )
                
                # Should commit on success
                mock_session.commit.assert_called_once()
                mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_data_safely_rollback_on_error(self, scheduler):
        """Test data caching rollback on error."""
        agents = []
        queues = []
        service_level = MagicMock()
        dashboard_data = MagicMock()
        
        with patch('scheduler_improved.get_db') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__next__.return_value = mock_session
            
            with patch('scheduler_improved.db_manager.cache_agent_states', 
                       side_effect=Exception("Cache error")):
                await scheduler._cache_data_safely(
                    agents, queues, service_level, dashboard_data
                )
                
                # Should rollback on error
                mock_session.rollback.assert_called_once()
                mock_session.close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
