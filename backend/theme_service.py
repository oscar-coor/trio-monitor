"""Theme service for managing automatic theme switching and custom theme settings."""

from datetime import datetime, time as dt_time
from typing import List, Optional
from sqlalchemy.orm import Session
from models import ThemeSchedule, ThemeSettings, ThemeType, ThemeStatusResponse
from database import ThemeScheduleDB, ThemeSettingsDB
import logging

logger = logging.getLogger(__name__)


class ThemeService:
    """Service for managing theme configuration and automatic switching."""
    
    def __init__(self):
        self.manual_override = False
        self.manual_theme = None
    
    def get_current_theme_by_time(self, db: Session) -> ThemeType:
        """Get current theme based on time and schedule."""
        if self.manual_override and self.manual_theme:
            return self.manual_theme
        
        current_time = datetime.now().time()
        current_weekday = datetime.now().weekday() + 1  # 1=Monday, 7=Sunday
        
        # Get active theme schedules
        schedules = db.query(ThemeScheduleDB).filter(ThemeScheduleDB.is_active == True).all()
        
        for schedule in schedules:
            if self._is_time_in_schedule(current_time, current_weekday, schedule):
                return ThemeType(schedule.theme_type)
        
        # Default to light theme if no schedule matches
        return ThemeType.LIGHT
    
    def _is_time_in_schedule(self, time: dt_time, weekday: int, schedule: ThemeScheduleDB) -> bool:
        """Check if current time matches a theme schedule."""
        # Check if current weekday is in the schedule
        if weekday not in schedule.weekdays:
            return False
        
        # Handle overnight schedules (e.g., 18:00-06:00)
        if schedule.start_time <= schedule.end_time:
            # Same day schedule (e.g., 09:00-17:00)
            return schedule.start_time <= time <= schedule.end_time
        else:
            # Overnight schedule (e.g., 18:00-06:00)
            return time >= schedule.start_time or time <= schedule.end_time
    
    def get_next_switch_time(self, db: Session) -> Optional[datetime]:
        """Get the next scheduled theme switch time."""
        current_time = datetime.now()
        current_weekday = current_time.weekday() + 1
        
        schedules = db.query(ThemeScheduleDB).filter(ThemeScheduleDB.is_active == True).all()
        
        next_switches = []
        for schedule in schedules:
            if current_weekday in schedule.weekdays:
                # Check start time today
                start_datetime = current_time.replace(
                    hour=schedule.start_time.hour,
                    minute=schedule.start_time.minute,
                    second=0,
                    microsecond=0
                )
                if start_datetime > current_time:
                    next_switches.append(start_datetime)
                
                # Check end time today
                end_datetime = current_time.replace(
                    hour=schedule.end_time.hour,
                    minute=schedule.end_time.minute,
                    second=0,
                    microsecond=0
                )
                if end_datetime > current_time:
                    next_switches.append(end_datetime)
        
        return min(next_switches) if next_switches else None
    
    def get_theme_status(self, db: Session) -> ThemeStatusResponse:
        """Get current theme status and information."""
        current_theme = self.get_current_theme_by_time(db)
        next_switch = self.get_next_switch_time(db)
        
        return ThemeStatusResponse(
            current_theme=current_theme,
            auto_theme_enabled=not self.manual_override,
            next_switch_time=next_switch,
            manual_override=self.manual_override
        )
    
    def set_manual_theme_override(self, theme: ThemeType) -> None:
        """Set manual theme override."""
        self.manual_override = True
        self.manual_theme = theme
        logger.info(f"Manual theme override set to: {theme}")
    
    def clear_manual_override(self) -> None:
        """Clear manual theme override and return to automatic."""
        self.manual_override = False
        self.manual_theme = None
        logger.info("Manual theme override cleared, returning to automatic")
    
    def get_theme_schedules(self, db: Session) -> List[ThemeSchedule]:
        """Get all theme schedules."""
        schedules_db = db.query(ThemeScheduleDB).all()
        return [self._schedule_db_to_model(schedule) for schedule in schedules_db]
    
    def update_theme_schedules(self, db: Session, schedules: List[ThemeSchedule]) -> List[ThemeSchedule]:
        """Update theme schedules configuration."""
        # Clear existing schedules
        db.query(ThemeScheduleDB).delete()
        
        # Add new schedules
        updated_schedules = []
        for schedule in schedules:
            schedule_db = ThemeScheduleDB(
                name=schedule.name,
                theme_type=schedule.theme_type.value,
                start_time=schedule.start_time,
                end_time=schedule.end_time,
                weekdays=schedule.weekdays,
                is_active=schedule.is_active
            )
            db.add(schedule_db)
            updated_schedules.append(schedule)
        
        db.commit()
        logger.info(f"Updated {len(schedules)} theme schedules")
        return updated_schedules
    
    def get_theme_settings(self, db: Session, theme_type: Optional[ThemeType] = None) -> List[ThemeSettings]:
        """Get theme settings, optionally filtered by theme type."""
        query = db.query(ThemeSettingsDB)
        if theme_type:
            query = query.filter(ThemeSettingsDB.theme_type == theme_type.value)
        
        settings_db = query.all()
        return [self._settings_db_to_model(setting) for setting in settings_db]
    
    def update_theme_settings(self, db: Session, settings: ThemeSettings) -> ThemeSettings:
        """Update or create theme settings."""
        settings_db = db.query(ThemeSettingsDB).filter(
            ThemeSettingsDB.theme_type == settings.theme_type.value
        ).first()
        
        if settings_db:
            # Update existing settings
            settings_db.primary_color = settings.primary_color
            settings_db.background_color = settings.background_color
            settings_db.surface_color = settings.surface_color
            settings_db.text_primary = settings.text_primary
            settings_db.text_secondary = settings.text_secondary
            settings_db.border_color = settings.border_color
            settings_db.success_color = settings.success_color
            settings_db.warning_color = settings.warning_color
            settings_db.error_color = settings.error_color
            settings_db.is_default = settings.is_default
            settings_db.updated_at = datetime.now()
        else:
            # Create new settings
            settings_db = ThemeSettingsDB(
                theme_type=settings.theme_type.value,
                primary_color=settings.primary_color,
                background_color=settings.background_color,
                surface_color=settings.surface_color,
                text_primary=settings.text_primary,
                text_secondary=settings.text_secondary,
                border_color=settings.border_color,
                success_color=settings.success_color,
                warning_color=settings.warning_color,
                error_color=settings.error_color,
                is_default=settings.is_default
            )
            db.add(settings_db)
        
        db.commit()
        db.refresh(settings_db)
        logger.info(f"Updated theme settings for: {settings.theme_type}")
        return self._settings_db_to_model(settings_db)
    
    def initialize_default_schedules(self, db: Session) -> None:
        """Initialize default theme schedules if none exist."""
        existing = db.query(ThemeScheduleDB).count()
        if existing > 0:
            return
        
        # Create default schedules
        light_schedule = ThemeScheduleDB(
            name="Dagstema",
            theme_type="light",
            start_time=dt_time(6, 0),  # 06:00
            end_time=dt_time(18, 0),   # 18:00
            weekdays=[1, 2, 3, 4, 5, 6, 7],  # All days
            is_active=True
        )
        
        dark_schedule = ThemeScheduleDB(
            name="Natttema",
            theme_type="dark",
            start_time=dt_time(18, 0),  # 18:00
            end_time=dt_time(6, 0),     # 06:00 (next day)
            weekdays=[1, 2, 3, 4, 5, 6, 7],  # All days
            is_active=True
        )
        
        db.add(light_schedule)
        db.add(dark_schedule)
        db.commit()
        logger.info("Initialized default theme schedules")
    
    def initialize_default_settings(self, db: Session) -> None:
        """Initialize default theme settings if none exist."""
        existing = db.query(ThemeSettingsDB).count()
        if existing > 0:
            return
        
        # Create default light theme settings
        light_settings = ThemeSettingsDB(
            theme_type="light",
            primary_color="#1976d2",
            background_color="#ffffff",
            surface_color="#f5f5f5",
            text_primary="#000000",
            text_secondary="#666666",
            border_color="#e0e0e0",
            success_color="#4caf50",
            warning_color="#ff9800",
            error_color="#f44336",
            is_default=True
        )
        
        # Create default dark theme settings
        dark_settings = ThemeSettingsDB(
            theme_type="dark",
            primary_color="#90caf9",
            background_color="#121212",
            surface_color="#1e1e1e",
            text_primary="#ffffff",
            text_secondary="#b0b0b0",
            border_color="#333333",
            success_color="#66bb6a",
            warning_color="#ffb74d",
            error_color="#ef5350",
            is_default=True
        )
        
        db.add(light_settings)
        db.add(dark_settings)
        db.commit()
        logger.info("Initialized default theme settings")
    
    def _schedule_db_to_model(self, schedule_db: ThemeScheduleDB) -> ThemeSchedule:
        """Convert database model to pydantic model."""
        return ThemeSchedule(
            id=schedule_db.id,
            name=schedule_db.name,
            theme_type=ThemeType(schedule_db.theme_type),
            start_time=schedule_db.start_time,
            end_time=schedule_db.end_time,
            weekdays=schedule_db.weekdays,
            is_active=schedule_db.is_active,
            created_at=schedule_db.created_at,
            updated_at=schedule_db.updated_at
        )
    
    def _settings_db_to_model(self, settings_db: ThemeSettingsDB) -> ThemeSettings:
        """Convert database model to pydantic model."""
        return ThemeSettings(
            id=settings_db.id,
            theme_type=ThemeType(settings_db.theme_type),
            primary_color=settings_db.primary_color,
            background_color=settings_db.background_color,
            surface_color=settings_db.surface_color,
            text_primary=settings_db.text_primary,
            text_secondary=settings_db.text_secondary,
            border_color=settings_db.border_color,
            success_color=settings_db.success_color,
            warning_color=settings_db.warning_color,
            error_color=settings_db.error_color,
            is_default=settings_db.is_default,
            created_at=settings_db.created_at,
            updated_at=settings_db.updated_at
        )


# Global theme service instance
theme_service = ThemeService()
