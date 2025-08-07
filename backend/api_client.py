"""API client for Trio Enterprise API integration."""

import asyncio
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
from models import AgentState, QueueMetrics, QueueStatus, AgentStatus, ServiceLevelMetrics
from auth import auth_manager
from config import settings
import logging

logger = logging.getLogger(__name__)


class TrioAPIClient:
    """Client for interacting with Trio Enterprise API."""
    
    def __init__(self):
        self.auth_manager = auth_manager
        self.queue_time_limit = settings.queue_time_limit
        self.warning_threshold = settings.warning_threshold
    
    async def _handle_api_request(self, endpoint: str, retry_on_redirect: bool = True):
        """Handle API requests with redirect support."""
        session = await self.auth_manager.get_session()
        response = await session.get(endpoint)
        
        # Handle 307 Temporary Redirect for failover
        if response.status_code == 307 and retry_on_redirect:
            logger.info(f"Handling redirect for endpoint: {endpoint}")
            await self.auth_manager._handle_redirect(response)
            # Retry with new session after redirect
            session = await self.auth_manager.get_session()
            response = await session.get(endpoint)
        
        response.raise_for_status()
        return response.json()

    async def get_agent_states(self) -> List[AgentState]:
        """Fetch current agent states from Trio API."""
        try:
            endpoint = f"/cc/{settings.trio_contact_center_id}/agents/state"
            agents_data = await self._handle_api_request(endpoint)
            agents = []
            
            # Handle both direct array and nested structure
            agent_list = agents_data if isinstance(agents_data, list) else agents_data.get("data", agents_data.get("agents", []))
            
            # Process agent data according to Trio API structure
            for agent_data in agent_list:
                # More robust field mapping based on actual Trio API responses
                agent = AgentState(
                    agent_id=str(agent_data.get("id", agent_data.get("agentId", ""))),
                    name=agent_data.get("name", agent_data.get("displayName", agent_data.get("firstName", "Unknown"))),
                    status=self._map_agent_status(agent_data.get("status", agent_data.get("state", "unavailable"))),
                    current_call_duration=agent_data.get("currentCallDuration", agent_data.get("current_call_duration")),
                    calls_handled_today=agent_data.get("callsHandledToday", agent_data.get("calls_handled_today", 0)),
                    average_call_time=agent_data.get("averageCallTime", agent_data.get("average_call_time")),
                    last_updated=datetime.now()
                )
                agents.append(agent)
            
            logger.info(f"Retrieved {len(agents)} agent states from Trio API")
            return agents
            
        except Exception as e:
            logger.error(f"Failed to fetch agent states: {e}")
            return self._get_mock_agent_states()  # Fallback for development
    
    async def get_queue_metrics(self) -> List[QueueMetrics]:
        """Fetch current queue metrics from Trio API."""
        try:
            endpoint = f"/cc/{settings.trio_contact_center_id}/services/state"
            queues_data = await self._handle_api_request(endpoint)
            queues = []
            
            # Handle both direct array and nested structure
            service_list = queues_data if isinstance(queues_data, list) else queues_data.get("data", queues_data.get("services", []))
            
            # Process queue data according to Trio API structure
            for queue_data in service_list:
                # More robust field mapping for different response formats
                wait_time = queue_data.get("currentWaitTime", queue_data.get("current_wait_time", 
                           queue_data.get("waitTime", 0)))
                
                queue = QueueMetrics(
                    queue_id=str(queue_data.get("id", queue_data.get("serviceId", ""))),
                    queue_name=queue_data.get("name", queue_data.get("serviceName", "Unknown Queue")),
                    current_wait_time=int(wait_time) if wait_time is not None else 0,
                    queue_depth=queue_data.get("queueDepth", queue_data.get("queue_depth", 
                               queue_data.get("queueLength", 0))),
                    status=self._determine_queue_status(int(wait_time) if wait_time is not None else 0),
                    calls_waiting=queue_data.get("callsWaiting", queue_data.get("calls_waiting", 
                                 queue_data.get("queueSize", 0))),
                    longest_wait_time=queue_data.get("longestWaitTime", queue_data.get("longest_wait_time", 0)),
                    average_wait_time=float(queue_data.get("averageWaitTime", queue_data.get("average_wait_time", 0.0))),
                    last_updated=datetime.now()
                )
                queues.append(queue)
            
            logger.info(f"Retrieved {len(queues)} queue metrics from Trio API")
            return queues
            
        except Exception as e:
            logger.error(f"Failed to fetch queue metrics: {e}")
            return self._get_mock_queue_metrics()  # Fallback for development
    
    async def get_service_level_metrics(self) -> ServiceLevelMetrics:
        """Fetch service level metrics from Trio API."""
        try:
            session = await self.auth_manager.get_session()
            # Use the correct Trio API endpoint for cases (to calculate service level)
            response = await session.get(f"/cc/{settings.trio_contact_center_id}/services/cases")
            response.raise_for_status()
            
            data = response.json()
            
            # Calculate service level metrics from cases data
            cases = data.get("cases", [])
            total_calls = len(cases)
            
            # Count calls answered within target time (20 seconds)
            calls_within_target = sum(1 for case in cases if case.get("wait_time", 0) <= self.queue_time_limit)
            
            service_level_percentage = (calls_within_target / total_calls * 100) if total_calls > 0 else 0.0
            
            # Calculate average wait time
            wait_times = [case.get("wait_time", 0) for case in cases]
            average_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0.0
            
            # Find peak wait time
            peak_wait_time = max(wait_times) if wait_times else 0
            
            # Calculate total queue time
            total_queue_time = sum(wait_times)
            
            # Check if queue time limit has been breached
            queue_time_limit_breached = total_queue_time >= self.queue_time_limit
            
            metrics = ServiceLevelMetrics(
                date=datetime.now(),
                total_calls=total_calls,
                calls_answered_within_target=calls_within_target,
                service_level_percentage=service_level_percentage,
                average_wait_time=average_wait_time,
                total_queue_time=total_queue_time,
                peak_wait_time=peak_wait_time,
                queue_time_limit_breached=queue_time_limit_breached
            )
            
            logger.info(f"Retrieved service level metrics: {service_level_percentage:.1f}%")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to fetch service level metrics: {e}")
            return self._get_mock_service_level()  # Fallback for development
    
    def _map_agent_status(self, status: str) -> AgentStatus:
        """Map Trio API agent status to internal status."""
        status_mapping = {
            "available": AgentStatus.AVAILABLE,
            "busy": AgentStatus.BUSY,
            "unavailable": AgentStatus.UNAVAILABLE,
            "break": AgentStatus.BREAK,
            "training": AgentStatus.TRAINING,
            "ready": AgentStatus.AVAILABLE,
            "on_call": AgentStatus.BUSY,
            "offline": AgentStatus.UNAVAILABLE
        }
        return status_mapping.get(status.lower(), AgentStatus.UNAVAILABLE)
    
    def _determine_queue_status(self, wait_time: int) -> QueueStatus:
        """Determine queue status based on wait time."""
        if wait_time >= self.queue_time_limit:
            return QueueStatus.CRITICAL
        elif wait_time >= self.warning_threshold:
            return QueueStatus.WARNING
        else:
            return QueueStatus.GOOD
    
    def _get_mock_agent_states(self) -> List[AgentState]:
        """Get mock agent states for development/testing."""
        return [
            AgentState(
                agent_id="agent_001",
                name="Anna Andersson",
                status=AgentStatus.AVAILABLE,
                calls_handled_today=12,
                average_call_time=180.5
            ),
            AgentState(
                agent_id="agent_002",
                name="Erik Eriksson",
                status=AgentStatus.BUSY,
                current_call_duration=145,
                calls_handled_today=8,
                average_call_time=220.3
            ),
            AgentState(
                agent_id="agent_003",
                name="Maria Johansson",
                status=AgentStatus.BREAK,
                calls_handled_today=15,
                average_call_time=165.8
            ),
            AgentState(
                agent_id="agent_004",
                name="Lars Larsson",
                status=AgentStatus.AVAILABLE,
                calls_handled_today=10,
                average_call_time=195.2
            )
        ]
    
    def _get_mock_queue_metrics(self) -> List[QueueMetrics]:
        """Get mock queue metrics for development/testing."""
        import random
        
        queues = []
        queue_names = ["Kundservice", "Teknisk Support", "Försäljning", "Fakturering"]
        
        for i, name in enumerate(queue_names):
            wait_time = random.randint(5, 25)  # Random wait time for demo
            
            queue = QueueMetrics(
                queue_id=f"queue_{i+1:03d}",
                queue_name=name,
                current_wait_time=wait_time,
                queue_depth=random.randint(0, 8),
                status=self._determine_queue_status(wait_time),
                calls_waiting=random.randint(0, 5),
                longest_wait_time=wait_time + random.randint(0, 10),
                average_wait_time=float(wait_time - random.randint(0, 5))
            )
            queues.append(queue)
        
        return queues
    
    def _get_mock_service_level(self) -> ServiceLevelMetrics:
        """Get mock service level metrics for development/testing."""
        total_calls = 150
        calls_within_target = 125
        
        return ServiceLevelMetrics(
            date=datetime.now(),
            total_calls=total_calls,
            calls_answered_within_target=calls_within_target,
            service_level_percentage=(calls_within_target / total_calls * 100),
            average_wait_time=16.5,
            total_queue_time=18,  # Close to 20s limit for demo
            peak_wait_time=28,
            queue_time_limit_breached=False
        )


# Global API client instance
api_client = TrioAPIClient()
