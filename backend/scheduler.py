"""Scheduler module for polling Trio Enterprise API."""

import asyncio
from datetime import datetime
from typing import Dict, Any, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from api_client import api_client
from database import get_db, db_manager
from models import DashboardData, AlertData, QueueStatus
from config import settings
import logging

logger = logging.getLogger(__name__)


class TrioScheduler:
    """Scheduler for periodic data polling and processing."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.latest_data: Dict[str, Any] = {}
        self.alerts: List[AlertData] = []
        self.is_running = False
        
    def start(self):
        """Start the scheduler."""
        if not self.is_running:
            # Schedule data polling every 10 seconds
            self.scheduler.add_job(
                self._poll_data,
                trigger=IntervalTrigger(seconds=settings.polling_interval),
                id="poll_trio_data",
                name="Poll Trio Enterprise API Data",
                max_instances=1
            )
            
            # Schedule cleanup every hour
            self.scheduler.add_job(
                self._cleanup_old_data,
                trigger=IntervalTrigger(hours=1),
                id="cleanup_data",
                name="Cleanup Old Data",
                max_instances=1
            )
            
            self.scheduler.start()
            self.is_running = True
            logger.info("Trio scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Trio scheduler stopped")
    
    async def _poll_data(self):
        """Poll data from Trio Enterprise API."""
        try:
            logger.info("Polling Trio Enterprise API...")
            
            # Fetch data from API
            agents = await api_client.get_agent_states()
            queues = await api_client.get_queue_metrics()
            service_level = await api_client.get_service_level_metrics()
            
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
            
            # Cache data in database
            db = next(get_db())
            try:
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
                        "average_wait_time": queue.average_wait_time
                    }
                    for queue in queues
                ]
                db_manager.cache_queue_metrics(db, queue_dicts)
                
                # Store historical data
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
                
            finally:
                db.close()
            
            # Update latest data
            self.latest_data = dashboard_data.dict()
            self.alerts = alerts
            
            logger.info(f"Successfully polled data: {len(agents)} agents, {len(queues)} queues")
            
        except Exception as e:
            logger.error(f"Error polling Trio API: {e}")
            self.latest_data["system_status"] = "error"
            self.latest_data["last_error"] = str(e)
    
    def _process_alerts(self, queues, service_level) -> List[AlertData]:
        """Process and generate alerts based on current data."""
        alerts = []
        current_time = datetime.now()
        
        # Check queue wait times
        for queue in queues:
            if queue.status == QueueStatus.CRITICAL:
                alert = AlertData(
                    alert_id=f"queue_critical_{queue.queue_id}_{int(current_time.timestamp())}",
                    type="queue_critical",
                    message=f"KRITISK: {queue.queue_name} har väntetid över {settings.queue_time_limit}s ({queue.current_wait_time}s)",
                    severity="critical",
                    timestamp=current_time
                )
                alerts.append(alert)
            
            elif queue.status == QueueStatus.WARNING:
                alert = AlertData(
                    alert_id=f"queue_warning_{queue.queue_id}_{int(current_time.timestamp())}",
                    type="queue_warning",
                    message=f"VARNING: {queue.queue_name} närmar sig gränsen ({queue.current_wait_time}s)",
                    severity="medium",
                    timestamp=current_time
                )
                alerts.append(alert)
        
        # Check service level
        if service_level.service_level_percentage < settings.service_level_target:
            alert = AlertData(
                alert_id=f"service_level_{int(current_time.timestamp())}",
                type="service_level",
                message=f"Servicenivå under mål: {service_level.service_level_percentage:.1f}% (mål: {settings.service_level_target}%)",
                severity="high",
                timestamp=current_time
            )
            alerts.append(alert)
        
        # Check total queue time limit
        if service_level.queue_time_limit_breached:
            alert = AlertData(
                alert_id=f"daily_limit_{int(current_time.timestamp())}",
                type="daily_limit",
                message=f"KRITISK: Daglig kötidsgräns överskriden ({service_level.total_queue_time}s av {settings.queue_time_limit}s)",
                severity="critical",
                timestamp=current_time
            )
            alerts.append(alert)
        
        return alerts
    
    async def _cleanup_old_data(self):
        """Clean up old data from database."""
        try:
            db = next(get_db())
            try:
                db_manager.cleanup_old_data(db, days_to_keep=30)
                logger.info("Cleaned up old data from database")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def get_latest_data(self) -> Dict[str, Any]:
        """Get the latest polled data."""
        return self.latest_data.copy() if self.latest_data else {}
    
    def get_alerts(self) -> List[AlertData]:
        """Get current alerts."""
        return self.alerts.copy()


# Global scheduler instance
trio_scheduler = TrioScheduler()
