"""Configuration module for Trio Monitor backend."""

import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Trio Enterprise API Configuration
    trio_api_base_url: str = os.getenv("TRIO_API_BASE_URL", "")
    trio_api_username: str = os.getenv("TRIO_API_USERNAME", "")
    trio_api_password: str = os.getenv("TRIO_API_PASSWORD", "")
    trio_api_token: str | None = os.getenv("TRIO_API_TOKEN")
    trio_contact_center_id: str = os.getenv("TRIO_CONTACT_CENTER_ID", "1")
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite")
    
    # Application Configuration
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    # When true, backend serves mock data instead of calling Trio API
    use_mock_data: bool = os.getenv("USE_MOCK_DATA", "False").lower() == "true"
    # In mock mode, default to faster polling (2s) unless explicitly overridden
    polling_interval: int = int(
        os.getenv(
            "POLLING_INTERVAL",
            "2" if os.getenv("USE_MOCK_DATA", "False").lower() == "true" else "10",
        )
    )
    cache_timeout: int = int(os.getenv("CACHE_TIMEOUT", "5"))
    queue_time_limit: int = int(os.getenv("QUEUE_TIME_LIMIT", "20"))
    warning_threshold: int = int(os.getenv("WARNING_THRESHOLD", "18"))
    service_level_target: int = int(os.getenv("SERVICE_LEVEL_TARGET", "80"))
    
    # CORS Configuration
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    # Comma-separated list of allowed origins for CORS, e.g. "https://monitor.urem.org,http://localhost:3000"
    allowed_origins: list[str] = [
        origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')},http://localhost:3000").split(",") if origin.strip()
    ]
    
    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()
