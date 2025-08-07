"""Admin API endpoints for managing monitored services, users, and configuration."""

from datetime import date, time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models import (
    MonitoredService, MonitoredUser, TimeWindow, SLAMetrics,
    TrioServiceInfo, TrioUserInfo, AdminConfigResponse,
    ThemeSchedule, ThemeSettings, ThemeType, ThemeStatusResponse
)
from database import get_db
from admin_service import admin_service
from theme_service import theme_service
import logging

logger = logging.getLogger(__name__)

# Create API router for admin endpoints
admin_router = APIRouter(prefix="/api/admin", tags=["admin"])
theme_router = APIRouter(prefix="/api/theme", tags=["theme"])


# ===== ADMIN CONFIGURATION ENDPOINTS =====

@admin_router.get("/services", response_model=List[TrioServiceInfo])
async def get_available_services():
    """Get all available services from Trio API."""
    try:
        return await admin_service.get_available_trio_services()
    except Exception as e:
        logger.error(f"Failed to get available services: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available services"
        )


@admin_router.get("/monitored-services", response_model=List[MonitoredService])
def get_monitored_services(db: Session = Depends(get_db)):
    """Get all monitored services."""
    return admin_service.get_monitored_services(db)


@admin_router.post("/monitored-services", response_model=MonitoredService)
def add_monitored_service(service: MonitoredService, db: Session = Depends(get_db)):
    """Add a new service to monitoring."""
    try:
        return admin_service.add_monitored_service(db, service)
    except Exception as e:
        logger.error(f"Failed to add monitored service: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add monitored service"
        )


@admin_router.put("/monitored-services/{service_id}", response_model=MonitoredService)
def update_monitored_service(
    service_id: int, 
    service: MonitoredService, 
    db: Session = Depends(get_db)
):
    """Update an existing monitored service."""
    updated_service = admin_service.update_monitored_service(db, service_id, service)
    if not updated_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitored service not found"
        )
    return updated_service


@admin_router.delete("/monitored-services/{service_id}")
def remove_monitored_service(service_id: int, db: Session = Depends(get_db)):
    """Remove a service from monitoring."""
    success = admin_service.remove_monitored_service(db, service_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitored service not found"
        )
    return {"message": "Service removed from monitoring"}


@admin_router.get("/users", response_model=List[TrioUserInfo])
async def get_available_users():
    """Get all available users/agents from Trio API."""
    try:
        return await admin_service.get_available_trio_users()
    except Exception as e:
        logger.error(f"Failed to get available users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available users"
        )


@admin_router.get("/monitored-users", response_model=List[MonitoredUser])
def get_monitored_users(db: Session = Depends(get_db)):
    """Get all monitored users."""
    return admin_service.get_monitored_users(db)


@admin_router.post("/monitored-users", response_model=MonitoredUser)
def add_monitored_user(user: MonitoredUser, db: Session = Depends(get_db)):
    """Add a new user to monitoring."""
    try:
        return admin_service.add_monitored_user(db, user)
    except Exception as e:
        logger.error(f"Failed to add monitored user: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add monitored user"
        )


@admin_router.put("/monitored-users/{user_id}", response_model=MonitoredUser)
def update_monitored_user(
    user_id: int, 
    user: MonitoredUser, 
    db: Session = Depends(get_db)
):
    """Update an existing monitored user."""
    updated_user = admin_service.update_monitored_user(db, user_id, user)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitored user not found"
        )
    return updated_user


@admin_router.delete("/monitored-users/{user_id}")
def remove_monitored_user(user_id: int, db: Session = Depends(get_db)):
    """Remove a user from monitoring."""
    success = admin_service.remove_monitored_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitored user not found"
        )
    return {"message": "User removed from monitoring"}


@admin_router.get("/time-windows", response_model=List[TimeWindow])
def get_time_windows(db: Session = Depends(get_db)):
    """Get all time windows configuration."""
    return admin_service.get_time_windows(db)


@admin_router.put("/time-windows", response_model=List[TimeWindow])
def update_time_windows(windows: List[TimeWindow], db: Session = Depends(get_db)):
    """Update time windows configuration."""
    try:
        return admin_service.update_time_windows(db, windows)
    except Exception as e:
        logger.error(f"Failed to update time windows: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update time windows"
        )


@admin_router.get("/sla-metrics", response_model=List[SLAMetrics])
def get_sla_metrics(
    service_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get SLA metrics with optional filters."""
    return admin_service.get_sla_metrics(db, service_id, date_from, date_to)


@admin_router.get("/config", response_model=AdminConfigResponse)
def get_admin_config(db: Session = Depends(get_db)):
    """Get complete admin configuration."""
    config = admin_service.get_admin_config(db)
    # Add theme schedule from theme service
    config.theme_schedule = theme_service.get_theme_schedules(db)
    return config


# ===== THEME CONFIGURATION ENDPOINTS =====

@theme_router.get("/current", response_model=ThemeType)
def get_current_theme(db: Session = Depends(get_db)):
    """Get current theme based on time and schedule."""
    return theme_service.get_current_theme_by_time(db)


@theme_router.get("/status", response_model=ThemeStatusResponse)
def get_theme_status(db: Session = Depends(get_db)):
    """Get current theme status and information."""
    return theme_service.get_theme_status(db)


@theme_router.post("/manual-override")
def set_manual_theme_override(theme: ThemeType):
    """Set manual theme override."""
    theme_service.set_manual_theme_override(theme)
    return {"message": f"Manual theme override set to {theme}"}


@theme_router.delete("/manual-override")
def clear_manual_override():
    """Clear manual theme override and return to automatic."""
    theme_service.clear_manual_override()
    return {"message": "Manual theme override cleared"}


@admin_router.get("/theme-schedule", response_model=List[ThemeSchedule])
def get_theme_schedules(db: Session = Depends(get_db)):
    """Get all theme schedules."""
    return theme_service.get_theme_schedules(db)


@admin_router.put("/theme-schedule", response_model=List[ThemeSchedule])
def update_theme_schedules(schedules: List[ThemeSchedule], db: Session = Depends(get_db)):
    """Update theme schedules configuration."""
    try:
        return theme_service.update_theme_schedules(db, schedules)
    except Exception as e:
        logger.error(f"Failed to update theme schedules: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update theme schedules"
        )


@admin_router.get("/theme-settings", response_model=List[ThemeSettings])
def get_theme_settings(
    theme_type: Optional[ThemeType] = None, 
    db: Session = Depends(get_db)
):
    """Get theme settings, optionally filtered by theme type."""
    return theme_service.get_theme_settings(db, theme_type)


@admin_router.put("/theme-settings", response_model=ThemeSettings)
def update_theme_settings(settings: ThemeSettings, db: Session = Depends(get_db)):
    """Update or create theme settings."""
    try:
        return theme_service.update_theme_settings(db, settings)
    except Exception as e:
        logger.error(f"Failed to update theme settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update theme settings"
        )


@admin_router.post("/initialize-defaults")
def initialize_default_configurations(db: Session = Depends(get_db)):
    """Initialize default theme schedules and settings."""
    try:
        theme_service.initialize_default_schedules(db)
        theme_service.initialize_default_settings(db)
        return {"message": "Default configurations initialized"}
    except Exception as e:
        logger.error(f"Failed to initialize defaults: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize default configurations"
        )


# Export routers for inclusion in main app
__all__ = ["admin_router", "theme_router"]
