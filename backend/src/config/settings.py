"""
Configuration management for the Access Control Manager.
"""
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = True
    reload: bool = True
    
    # CORS Configuration
    frontend_url: str = "http://localhost:3000"
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # WebSocket Configuration
    ws_endpoint: str = "/ws"
    ws_ping_interval: int = 25
    ws_ping_timeout: int = 20
    
    # API Configuration
    api_prefix: str = "/api"
    api_title: str = "Access Control Manager API"
    api_description: str = "A real-time access control system for smart doors"
    api_version: str = "1.0.0"
    
    # Security Configuration
    admin_user_id: str = "admin"
    default_user_timeout: int = 300
    
    # Rate Limiting Configuration
    rate_limit_max_attempts_per_minute: int = 20
    rate_limit_max_failed_attempts: int = 5
    rate_limit_lockout_duration_minutes: int = 1
    rate_limit_cleanup_interval_minutes: int = 60
    
    # Device Configuration
    default_device_count: int = 2
    device_state_broadcast: bool = True
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Environment
    environment: str = "development"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert allowed_origins string to list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()