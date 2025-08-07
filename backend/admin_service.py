"""Admin service for managing monitored services, users, and SLA configurations."""

from datetime import datetime, date, time as dt_time
from typing import List, Optional
from sqlalchemy.orm import Session
from models import (
    MonitoredService, MonitoredUser, TimeWindow, SLAMetrics,
    TrioServiceInfo, TrioUserInfo, AdminConfigResponse
)
from database import (
    MonitoredServiceDB, MonitoredUserDB, TimeWindowDB, SLAMetricsDB,
    get_db
)
from auth import auth_manager
from config import settings
import logging

logger = logging.getLogger(__name__)


class AdminService:
    """Service for managing admin configuration."""
    
    def __init__(self):
        self.auth_manager = auth_manager
    
    async def get_available_trio_services(self) -> List[TrioServiceInfo]:
        """Get all available services from Trio API."""
        try:
            session = await self.auth_manager.get_session()
            response = await session.get(f"/cc/{settings.trio_contact_center_id}/services")
            response.raise_for_status()
            
            services_data = response.json()
            services = []
            
            # Handle both direct array and nested structure
            service_list = services_data if isinstance(services_data, list) else services_data.get("data", services_data.get("services", []))
            
            for service_data in service_list:
                service = TrioServiceInfo(
                    id=str(service_data.get("id", service_data.get("serviceId", ""))),
                    name=service_data.get("name", service_data.get("serviceName", "Unknown Service")),
                    description=service_data.get("description", ""),
                    is_active=service_data.get("isActive", service_data.get("active", True))
                )
                services.append(service)
            
            logger.info(f"Retrieved {len(services)} available services from Trio API")
            return services
            
        except Exception as e:
            logger.error(f"Failed to fetch available services: {e}")
            # Return mock data for development
            return [
                TrioServiceInfo(id="svc_001", name="Kundservice", description="Allmän kundservice"),
                TrioServiceInfo(id="svc_002", name="Teknisk Support", description="Teknisk support"),
                TrioServiceInfo(id="svc_003", name="Försäljning", description="Säljstöd och kampanjer"),
                TrioServiceInfo(id="svc_004", name="Fakturering", description="Fakturafrågor och betalningar")
            ]
    
    async def get_available_trio_users(self) -> List[TrioUserInfo]:
        """Get all available users/agents from Trio API."""
        try:
            session = await self.auth_manager.get_session()
            response = await session.get(f"/cc/{settings.trio_contact_center_id}/agents")
            response.raise_for_status()
            
            users_data = response.json()
            users = []
            
            # Handle both direct array and nested structure
            user_list = users_data if isinstance(users_data, list) else users_data.get("data", users_data.get("agents", []))
            
            for user_data in user_list:
                user = TrioUserInfo(
                    id=str(user_data.get("id", user_data.get("agentId", ""))),
                    name=user_data.get("name", user_data.get("userName", "Unknown User")),
                    display_name=user_data.get("displayName", user_data.get("firstName", "")),
                    email=user_data.get("email", ""),
                    is_active=user_data.get("isActive", user_data.get("active", True))
                )
                users.append(user)
            
            logger.info(f"Retrieved {len(users)} available users from Trio API")
            return users
            
        except Exception as e:
            logger.error(f"Failed to fetch available users: {e}")
            # Return mock data for development
            return [
                TrioUserInfo(id="usr_001", name="anna.andersson", display_name="Anna Andersson"),
                TrioUserInfo(id="usr_002", name="erik.eriksson", display_name="Erik Eriksson"),
                TrioUserInfo(id="usr_003", name="maria.johansson", display_name="Maria Johansson"),
                TrioUserInfo(id="usr_004", name="lars.larsson", display_name="Lars Larsson")
            ]
    
    def get_monitored_services(self, db: Session) -> List[MonitoredService]:
        """Get all monitored services from database."""
        services_db = db.query(MonitoredServiceDB).all()
        return [self._service_db_to_model(service) for service in services_db]
    
    def add_monitored_service(self, db: Session, service: MonitoredService) -> MonitoredService:
        """Add a new service to monitoring."""
        service_db = MonitoredServiceDB(
            trio_service_id=service.trio_service_id,
            service_name=service.service_name,
            sla_target_seconds=service.sla_target_seconds,
            warning_threshold_seconds=service.warning_threshold_seconds,
            is_active=service.is_active
        )
        db.add(service_db)
        db.commit()
        db.refresh(service_db)
        
        logger.info(f"Added monitored service: {service.service_name}")
        return self._service_db_to_model(service_db)
    
    def update_monitored_service(self, db: Session, service_id: int, service: MonitoredService) -> Optional[MonitoredService]:
        """Update an existing monitored service."""
        service_db = db.query(MonitoredServiceDB).filter(MonitoredServiceDB.id == service_id).first()
        if not service_db:
            return None
        
        service_db.service_name = service.service_name
        service_db.sla_target_seconds = service.sla_target_seconds
        service_db.warning_threshold_seconds = service.warning_threshold_seconds
        service_db.is_active = service.is_active
        service_db.updated_at = datetime.now()
        
        db.commit()
        logger.info(f"Updated monitored service: {service.service_name}")
        return self._service_db_to_model(service_db)
    
    def remove_monitored_service(self, db: Session, service_id: int) -> bool:
        """Remove a service from monitoring."""
        service_db = db.query(MonitoredServiceDB).filter(MonitoredServiceDB.id == service_id).first()
        if not service_db:
            return False
        
        db.delete(service_db)
        db.commit()
        logger.info(f"Removed monitored service ID: {service_id}")
        return True
    
    def get_monitored_users(self, db: Session) -> List[MonitoredUser]:
        """Get all monitored users from database."""
        users_db = db.query(MonitoredUserDB).all()
        return [self._user_db_to_model(user) for user in users_db]
    
    def add_monitored_user(self, db: Session, user: MonitoredUser) -> MonitoredUser:
        """Add a new user to monitoring."""
        user_db = MonitoredUserDB(
            trio_user_id=user.trio_user_id,
            user_name=user.user_name,
            display_name=user.display_name,
            is_active=user.is_active
        )
        db.add(user_db)
        db.commit()
        db.refresh(user_db)
        
        logger.info(f"Added monitored user: {user.user_name}")
        return self._user_db_to_model(user_db)
    
    def update_monitored_user(self, db: Session, user_id: int, user: MonitoredUser) -> Optional[MonitoredUser]:
        """Update an existing monitored user."""
        user_db = db.query(MonitoredUserDB).filter(MonitoredUserDB.id == user_id).first()
        if not user_db:
            return None
        
        user_db.user_name = user.user_name
        user_db.display_name = user.display_name
        user_db.is_active = user.is_active
        user_db.updated_at = datetime.now()
        
        db.commit()
        logger.info(f"Updated monitored user: {user.user_name}")
        return self._user_db_to_model(user_db)
    
    def remove_monitored_user(self, db: Session, user_id: int) -> bool:
        """Remove a user from monitoring."""
        user_db = db.query(MonitoredUserDB).filter(MonitoredUserDB.id == user_id).first()
        if not user_db:
            return False
        
        db.delete(user_db)
        db.commit()
        logger.info(f"Removed monitored user ID: {user_id}")
        return True
    
    def get_time_windows(self, db: Session) -> List[TimeWindow]:
        """Get all time windows from database."""
        windows_db = db.query(TimeWindowDB).all()
        return [self._time_window_db_to_model(window) for window in windows_db]
    
    def update_time_windows(self, db: Session, windows: List[TimeWindow]) -> List[TimeWindow]:
        """Update time windows configuration."""
        # Clear existing windows
        db.query(TimeWindowDB).delete()
        
        # Add new windows
        updated_windows = []
        for window in windows:
            window_db = TimeWindowDB(
                name=window.name,
                start_time=window.start_time,
                end_time=window.end_time,
                weekdays=window.weekdays,
                is_active=window.is_active
            )
            db.add(window_db)
            updated_windows.append(window)
        
        db.commit()
        logger.info(f"Updated {len(windows)} time windows")
        return updated_windows
    
    def get_sla_metrics(self, db: Session, service_id: Optional[int] = None, 
                       date_from: Optional[date] = None, date_to: Optional[date] = None) -> List[SLAMetrics]:
        """Get SLA metrics with optional filters."""
        query = db.query(SLAMetricsDB)
        
        if service_id:
            query = query.filter(SLAMetricsDB.service_id == service_id)
        if date_from:
            query = query.filter(SLAMetricsDB.measurement_date >= date_from)
        if date_to:
            query = query.filter(SLAMetricsDB.measurement_date <= date_to)
        
        metrics_db = query.all()
        return [self._sla_metrics_db_to_model(metric) for metric in metrics_db]
    
    def get_admin_config(self, db: Session) -> AdminConfigResponse:
        """Get complete admin configuration."""
        return AdminConfigResponse(
            monitored_services=self.get_monitored_services(db),
            monitored_users=self.get_monitored_users(db),
            time_windows=self.get_time_windows(db),
            theme_schedule=[]  # Will be populated by theme service
        )
    
    def _service_db_to_model(self, service_db: MonitoredServiceDB) -> MonitoredService:
        """Convert database model to pydantic model."""
        return MonitoredService(
            id=service_db.id,
            trio_service_id=service_db.trio_service_id,
            service_name=service_db.service_name,
            sla_target_seconds=service_db.sla_target_seconds,
            warning_threshold_seconds=service_db.warning_threshold_seconds,
            is_active=service_db.is_active,
            created_at=service_db.created_at,
            updated_at=service_db.updated_at
        )
    
    def _user_db_to_model(self, user_db: MonitoredUserDB) -> MonitoredUser:
        """Convert database model to pydantic model."""
        return MonitoredUser(
            id=user_db.id,
            trio_user_id=user_db.trio_user_id,
            user_name=user_db.user_name,
            display_name=user_db.display_name,
            is_active=user_db.is_active,
            created_at=user_db.created_at,
            updated_at=user_db.updated_at
        )
    
    def _time_window_db_to_model(self, window_db: TimeWindowDB) -> TimeWindow:
        """Convert database model to pydantic model."""
        return TimeWindow(
            id=window_db.id,
            name=window_db.name,
            start_time=window_db.start_time,
            end_time=window_db.end_time,
            weekdays=window_db.weekdays,
            is_active=window_db.is_active,
            created_at=window_db.created_at,
            updated_at=window_db.updated_at
        )
    
    def _sla_metrics_db_to_model(self, metrics_db: SLAMetricsDB) -> SLAMetrics:
        """Convert database model to pydantic model."""
        return SLAMetrics(
            id=metrics_db.id,
            service_id=metrics_db.service_id,
            measurement_date=metrics_db.measurement_date,
            time_window_id=metrics_db.time_window_id,
            average_wait_time=metrics_db.average_wait_time,
            total_calls=metrics_db.total_calls,
            calls_within_sla=metrics_db.calls_within_sla,
            sla_percentage=metrics_db.sla_percentage,
            peak_wait_time=metrics_db.peak_wait_time,
            created_at=metrics_db.created_at
        )


# Global admin service instance
admin_service = AdminService()
