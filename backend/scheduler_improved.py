"""Improved scheduler module for polling Trio Enterprise API."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session
import logging

from api_client import api_client
from database import db_manager, get_db
from models import DashboardData, AlertData, QueueStatus
from config import settings

logger = logging.getLogger(__name__)

# Constants for magic numbers
CRITICAL_WAIT_TIME = settings.queue_time_limit  # 20 seconds
WARNING_WAIT_TIME = settings.warning_threshold   # 15-18 seconds
SERVICE_LEVEL_TARGET = settings.service_level_target  # 80%
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


class ImprovedTrioScheduler:
    """Enhanced scheduler with better error handling and resource management."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.latest_data: Dict[str, Any] = {}
        self.alerts: List[AlertData] = []
        self.is_running = False
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5
        
    def start(self):
        """Start the scheduler with proper error handling."""
        if not self.is_running:
            try:
                # Schedule data polling every 10 seconds
                self.scheduler.add_job(
                    self._poll_data_with_retry,
                    trigger=IntervalTrigger(seconds=settings.polling_interval),
                    id="poll_trio_data",
                    name="Poll Trio Enterprise API Data",
                    max_instances=1,
                    misfire_grace_time=5
                )
                
                # Schedule cleanup every hour
                self.scheduler.add_job(
                    self._cleanup_old_data,
                    trigger=IntervalTrigger(hours=1),
                    id="cleanup_data",
                    name="Cleanup Old Data",
                    max_instances=1
                )
                
                # Schedule health check every minute
                self.scheduler.add_job(
                    self._health_check,
                    trigger=IntervalTrigger(minutes=1),
                    id="health_check",
                    name="System Health Check",
                    max_instances=1
                )
                
                self.scheduler.start()
                self.is_running = True
                logger.info("Enhanced Trio scheduler started successfully")
            except Exception as e:
                logger.error(f"Failed to start scheduler: {e}", exc_info=True)
                raise
    
    def stop(self):
        """Stop the scheduler gracefully."""
        if self.is_running:
            try:
                self.scheduler.shutdown(wait=True)
                self.is_running = False
                logger.info("Trio scheduler stopped gracefully")
            except Exception as e:
                logger.error(f"Error stopping scheduler: {e}", exc_info=True)
    
    async def _poll_data_with_retry(self):
        """Poll data with retry logic and circuit breaker pattern."""
        # Circuit breaker: stop trying if too many consecutive failures
        if self.consecutive_failures >= self.max_consecutive_failures:
            logger.error(f"Circuit breaker activated after {self.consecutive_failures} failures")
            self.latest_data["system_status"] = "circuit_breaker_open"
            
            # Try to reset after some time
            if self.consecutive_failures % 10 == 0:  # Try every 10th attempt
                logger.info("Attempting to reset circuit breaker...")
            else:
                return
        
        for attempt in range(MAX_RETRIES):
            try:
                await self._poll_data()
                self.consecutive_failures = 0  # Reset on success
                return
            except asyncio.TimeoutError:
                logger.warning(f"Polling timeout on attempt {attempt + 1}/{MAX_RETRIES}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
            except Exception as e:
                logger.error(f"Polling error on attempt {attempt + 1}/{MAX_RETRIES}: {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
        
        # All retries failed
        self.consecutive_failures += 1
        logger.error(f"All polling attempts failed. Consecutive failures: {self.consecutive_failures}")
        self.latest_data["system_status"] = "degraded"
    
    async def _poll_data(self):
        """Poll data from Trio Enterprise API with proper resource management."""
        logger.info("Starting Trio Enterprise API polling...")
        
        try:
            # Fetch data from API with timeout
            agents = await asyncio.wait_for(
                api_client.get_agent_states(), 
                timeout=10.0
            )
            queues = await asyncio.wait_for(
                api_client.get_queue_metrics(), 
                timeout=10.0
            )
            service_level = await asyncio.wait_for(
                api_client.get_service_level_metrics(), 
                timeout=10.0
            )
            
            # Process alerts
            alerts = self._process_alerts(queues, service_level)
            
            # Create dashboard data
            dashboard_data = DashboardData(
                agents=agents,
                queues=queues,
                service_level=service_level,
                system_status="operational",
                alerts=[alert.message for alert in alerts],
                last_updated=datetime.now()
            )
            
            # Cache data in database with proper session management
            await self._cache_data_safely(agents, queues, service_level, dashboard_data)
            
            # Update latest data
            self.latest_data = dashboard_data.dict()
            self.alerts = alerts
            
            logger.info(f"Successfully polled: {len(agents)} agents, {len(queues)} queues")
            
        except asyncio.TimeoutError:
            logger.error("API polling timeout exceeded")
            raise
        except Exception as e:
            logger.error(f"Error during polling: {e}", exc_info=True)
            self.latest_data["system_status"] = "error"
            self.latest_data["last_error"] = str(e)
            raise
    
    async def _cache_data_safely(self, agents, queues, service_level, dashboard_data):
        """Cache data with proper database session management."""
        db = None
        try:
            # Get database session properly
            db_gen = get_db()
            db = next(db_gen)
            
            # Cache agent states
            agent_dicts = [
                {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "status": agent.status.value,
                    "current_call_duration": agent.current_call_duration,
                    "calls_handled_today": agent.calls_handled_today,
                    "average_call_time": agent.average_call_time
                }
                for agent in agents
            ]
            db_manager.cache_agent_states(db, agent_dicts)
            
            # Cache queue metrics
            queue_dicts = [
                {
                    "queue_id": queue.queue_id,
                    "queue_name": queue.queue_name,
                    "current_wait_time": queue.current_wait_time,
                    "queue_depth": queue.queue_depth,
                    "status": queue.status.value,
                    "calls_waiting": queue.calls_waiting,
                    "longest_wait_time": queue.longest_wait_time,
                    "average_wait_time": queue.average_wait_time,
                    "timestamp": datetime.now()
                }
                for queue in queues
            ]
            db_manager.cache_queue_metrics(db, queue_dicts)
            
            # Store historical data for each queue
            for queue in queues:
                historical_data = {
                    "timestamp": datetime.now(),
                    "queue_id": queue.queue_id,
                    "wait_time": queue.current_wait_time,
                    "queue_depth": queue.queue_depth,
                    "service_level": service_level.service_level_percentage,
                    "total_agents": len(agents),
                    "available_agents": len([a for a in agents if a.status.value == "available"])
                }
                db_manager.store_historical_data(db, historical_data)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Database caching error: {e}", exc_info=True)
            if db:
                db.rollback()
        finally:
            # Ensure database session is properly closed
            if db:
                try:
                    db.close()
                except:
                    pass
            # Properly close the generator
            try:
                db_gen.close()
            except:
                pass
    
    def _process_alerts(self, queues, service_level) -> List[AlertData]:
        """Process and generate alerts with proper thresholds."""
        alerts = []
        current_time = datetime.now()
        
        # Check queue wait times with constants
        for queue in queues:
            if queue.current_wait_time >= CRITICAL_WAIT_TIME:
                alert = AlertData(
                    alert_id=f"queue_critical_{queue.queue_id}_{int(current_time.timestamp())}",
                    type="queue_critical",
                    message=f"KRITISK: {queue.queue_name} har väntetid över {CRITICAL_WAIT_TIME}s ({queue.current_wait_time}s)",
                    severity="critical",
                    timestamp=current_time
                )
                alerts.append(alert)
            
            elif queue.current_wait_time >= WARNING_WAIT_TIME:
                alert = AlertData(
                    alert_id=f"queue_warning_{queue.queue_id}_{int(current_time.timestamp())}",
                    type="queue_warning",
                    message=f"VARNING: {queue.queue_name} närmar sig gränsen ({queue.current_wait_time}s)",
                    severity="medium",
                    timestamp=current_time
                )
                alerts.append(alert)
        
        # Check service level with constant
        if service_level.service_level_percentage < SERVICE_LEVEL_TARGET:
            alert = AlertData(
                alert_id=f"service_level_{int(current_time.timestamp())}",
                type="service_level",
                message=f"Servicenivå under mål: {service_level.service_level_percentage:.1f}% (mål: {SERVICE_LEVEL_TARGET}%)",
                severity="high",
                timestamp=current_time
            )
            alerts.append(alert)
        
        # Check total queue time limit
        if service_level.queue_time_limit_breached:
            alert = AlertData(
                alert_id=f"daily_limit_{int(current_time.timestamp())}",
                type="daily_limit",
                message=f"KRITISK: Daglig kötidsgräns överskriden ({service_level.total_queue_time}s av {CRITICAL_WAIT_TIME}s)",
                severity="critical",
                timestamp=current_time
            )
            alerts.append(alert)
        
        return alerts
    
    async def _cleanup_old_data(self):
        """Clean up old data from database with error handling."""
        try:
            db_gen = get_db()
            db = next(db_gen)
            try:
                db_manager.cleanup_old_data(db, days_to_keep=30)
                logger.info("Successfully cleaned up old data")
            finally:
                db.close()
                db_gen.close()
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}", exc_info=True)
    
    async def _health_check(self):
        """Perform system health check."""
        try:
            # Check API connectivity
            api_healthy = await api_client.test_connection()
            
            # Check database connectivity
            db_healthy = False
            try:
                db_gen = get_db()
                db = next(db_gen)
                db.execute("SELECT 1")
                db_healthy = True
                db.close()
                db_gen.close()
            except:
                pass
            
            # Update system status
            if api_healthy and db_healthy:
                if self.latest_data.get("system_status") != "operational":
                    logger.info("System health restored to operational")
                    self.latest_data["system_status"] = "operational"
            elif not api_healthy:
                logger.warning("API health check failed")
                self.latest_data["system_status"] = "api_unreachable"
            elif not db_healthy:
                logger.warning("Database health check failed")
                self.latest_data["system_status"] = "database_error"
                
        except Exception as e:
            logger.error(f"Health check error: {e}", exc_info=True)
    
    def get_latest_data(self) -> Dict[str, Any]:
        """Get the latest polled data."""
        return self.latest_data.copy() if self.latest_data else {}
    
    def get_alerts(self) -> List[AlertData]:
        """Get current alerts."""
        return self.alerts.copy()
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics."""
        return {
            "is_running": self.is_running,
            "consecutive_failures": self.consecutive_failures,
            "circuit_breaker_status": "open" if self.consecutive_failures >= self.max_consecutive_failures else "closed",
            "last_successful_poll": self.latest_data.get("last_updated"),
            "system_status": self.latest_data.get("system_status", "unknown")
        }


# Global scheduler instance
trio_scheduler = ImprovedTrioScheduler()
