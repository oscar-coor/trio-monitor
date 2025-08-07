"""Improved configuration module with validation and security."""

import os
from typing import Optional, List
from pydantic import BaseSettings, Field, validator, SecretStr
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ImprovedSettings(BaseSettings):
    """Enhanced settings with validation and secure defaults."""
    
    # API Configuration
    trio_api_base_url: str = Field(
        default="https://api.trio-enterprise.com",
        description="Base URL for Trio Enterprise API"
    )
    trio_username: Optional[str] = Field(
        default=None,
        description="Username for API authentication"
    )
    trio_password: Optional[SecretStr] = Field(
        default=None,
        description="Password for API authentication (stored securely)"
    )
    trio_token: Optional[SecretStr] = Field(
        default=None,
        description="API token for authentication"
    )
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./trio_monitor.db",
        description="Database connection URL"
    )
    database_pool_size: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Database connection pool size"
    )
    
    # Polling Configuration
    polling_interval: int = Field(
        default=10,
        ge=5,
        le=60,
        description="Polling interval in seconds"
    )
    
    # Queue Time Limits (in seconds)
    queue_time_limit: int = Field(
        default=20,
        ge=10,
        le=60,
        description="Critical queue time limit in seconds"
    )
    warning_threshold: int = Field(
        default=15,
        ge=5,
        le=60,
        description="Warning threshold for queue time in seconds"
    )
    
    # Service Level Configuration
    service_level_target: float = Field(
        default=80.0,
        ge=50.0,
        le=100.0,
        description="Service level target percentage"
    )
    service_level_time_window: int = Field(
        default=20,
        ge=10,
        le=60,
        description="Time window for service level calculation in seconds"
    )
    
    # Frontend Configuration
    frontend_url: str = Field(
        default="http://localhost:3000",
        description="Frontend URL for CORS configuration"
    )
    allowed_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        description="Allowed CORS origins"
    )
    
    # Security Configuration
    secret_key: SecretStr = Field(
        default=SecretStr("change-this-in-production"),
        description="Secret key for encryption and sessions"
    )
    password_salt: SecretStr = Field(
        default=SecretStr("change-this-salt"),
        description="Salt for password hashing"
    )
    enable_https: bool = Field(
        default=True,
        description="Enforce HTTPS in production"
    )
    
    # Application Configuration
    debug: bool = Field(
        default=False,
        description="Debug mode"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level",
        regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
    )
    max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of API retry attempts"
    )
    retry_delay: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Delay between retries in seconds"
    )
    
    # Performance Configuration
    cache_ttl: int = Field(
        default=300,
        ge=60,
        le=3600,
        description="Cache time-to-live in seconds"
    )
    max_cache_size: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Maximum cache size in entries"
    )
    
    # Alert Configuration
    alert_cooldown: int = Field(
        default=300,
        ge=60,
        le=1800,
        description="Cooldown period for similar alerts in seconds"
    )
    max_alerts_per_hour: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Maximum alerts per hour to prevent spam"
    )
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    @validator("trio_password", "trio_token", "secret_key", "password_salt")
    def validate_secrets(cls, v, field):
        """Validate that secrets are not default values in production."""
        if v and not os.getenv("DEBUG", "").lower() == "true":
            default_values = ["change-this", "default", "example", "test"]
            value_str = v.get_secret_value() if hasattr(v, 'get_secret_value') else str(v)
            if any(default in value_str.lower() for default in default_values):
                logger.warning(f"⚠️ {field.name} contains default value - please change for production!")
        return v
    
    @validator("trio_username")
    def validate_authentication(cls, v, values):
        """Validate that either token or username/password is provided."""
        if not v and not values.get("trio_token"):
            raise ValueError("Either trio_token or trio_username/trio_password must be provided")
        return v
    
    @validator("warning_threshold")
    def validate_thresholds(cls, v, values):
        """Validate that warning threshold is less than critical limit."""
        if "queue_time_limit" in values and v >= values["queue_time_limit"]:
            raise ValueError(f"Warning threshold ({v}) must be less than queue time limit ({values['queue_time_limit']})")
        return v
    
    @validator("allowed_origins", pre=True)
    def parse_allowed_origins(cls, v):
        """Parse allowed origins from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("database_url")
    def validate_database_url(cls, v):
        """Validate and prepare database URL."""
        if v.startswith("sqlite"):
            # Ensure SQLite database directory exists
            db_path = v.replace("sqlite:///", "")
            db_dir = Path(db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using SQLite database at: {db_path}")
        return v
    
    def get_safe_config(self) -> dict:
        """Get configuration without sensitive values for logging."""
        config = self.dict()
        sensitive_keys = ["trio_password", "trio_token", "secret_key", "password_salt"]
        for key in sensitive_keys:
            if key in config and config[key]:
                config[key] = "***REDACTED***"
        return config
    
    def validate_production_settings(self):
        """Validate settings for production deployment."""
        errors = []
        
        if not self.debug:
            # Production validations
            if self.secret_key.get_secret_value() == "change-this-in-production":
                errors.append("Secret key must be changed for production")
            
            if self.password_salt.get_secret_value() == "change-this-salt":
                errors.append("Password salt must be changed for production")
            
            if not self.enable_https:
                errors.append("HTTPS should be enabled in production")
            
            if "localhost" in self.trio_api_base_url:
                errors.append("API base URL should not use localhost in production")
            
            if self.database_url.startswith("sqlite"):
                logger.warning("SQLite is not recommended for production - consider PostgreSQL")
        
        if errors:
            raise ValueError(f"Production configuration errors: {'; '.join(errors)}")
    
    def setup_logging(self):
        """Configure logging based on settings."""
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Suppress noisy libraries
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        
        logger.info(f"Logging configured at {self.log_level} level")


# Load and validate settings
try:
    settings = ImprovedSettings()
    settings.setup_logging()
    
    # Log safe configuration
    logger.info("Configuration loaded successfully")
    logger.debug(f"Configuration: {settings.get_safe_config()}")
    
    # Validate production settings if not in debug mode
    if not settings.debug:
        settings.validate_production_settings()
        
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    raise


# Export commonly used settings
CRITICAL_WAIT_TIME = settings.queue_time_limit
WARNING_WAIT_TIME = settings.warning_threshold
SERVICE_LEVEL_TARGET = settings.service_level_target
POLLING_INTERVAL = settings.polling_interval
