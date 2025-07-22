# core/config.py

from pydantic_settings import BaseSettings
from pydantic import validator
from typing import Optional, List
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application settings
    app_name: str = "Talktor Medical Interpreter"
    app_version: str = "2.0.0"
    debug: bool = False
    environment: str = "development"  # development, staging, production
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    
    # Database settings
    database_url: str = "sqlite:///./talktor.db"  # Default to SQLite for development
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_pre_ping: bool = True
    
    # Security settings
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    
    # CORS settings
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # External API settings
    rxnorm_api_base_url: str = "https://rxnav.nlm.nih.gov/REST"
    fda_api_base_url: str = "https://api.fda.gov"
    api_request_timeout: int = 10
    api_retry_attempts: int = 3
    api_cache_ttl_seconds: int = 3600  # 1 hour
    
    # Machine Learning settings
    whisper_model: str = "base"  # base, small, medium, large
    extraction_confidence_threshold: float = 0.6
    learning_feedback_required: int = 10  # Minimum feedback for RL training
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None
    
    # Feature flags
    enable_learning: bool = True
    enable_feedback_collection: bool = True
    enable_analytics: bool = True
    enable_caching: bool = True
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10
    
    # File upload settings
    max_file_size_mb: int = 10
    allowed_audio_formats: List[str] = ["wav", "mp3", "m4a", "flac"]
    upload_temp_dir: str = "/tmp/talktor_uploads"
    
    @validator("database_url")
    def validate_database_url(cls, v):
        """Validate database URL format"""
        if not v:
            raise ValueError("Database URL cannot be empty")
        return v
    
    @validator("cors_origins")
    def validate_cors_origins(cls, v):
        """Ensure CORS origins are properly formatted"""
        if isinstance(v, str):
            return [v]
        return v
    
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment setting"""
        allowed_envs = ["development", "staging", "production"]
        if v not in allowed_envs:
            raise ValueError(f"Environment must be one of: {allowed_envs}")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Global settings instance
settings = Settings()