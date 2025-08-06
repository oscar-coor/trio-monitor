"""Configuration module for Trio Monitor backend."""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Trio Enterprise API Configuration
    trio_api_base_url: str = os.getenv("TRIO_API_BASE_URL", "")
    trio_api_username: str = os.getenv("TRIO_API_USERNAME", "")
    trio_api_password: str = os.getenv("TRIO_API_PASSWORD", "")
    trio_api_token: Optional[str] = os.getenv("TRIO_API_TOKEN")
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite")
    
    # Application Configuration
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    polling_interval: int = int(os.getenv("POLLING_INTERVAL", "10"))
    cache_timeout: int = int(os.getenv("CACHE_TIMEOUT", "5"))
    queue_time_limit: int = int(os.getenv("QUEUE_TIME_LIMIT", "20"))
    warning_threshold: int = int(os.getenv("WARNING_THRESHOLD", "18"))
    service_level_target: int = int(os.getenv("SERVICE_LEVEL_TARGET", "80"))
    
    # CORS Configuration
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()
