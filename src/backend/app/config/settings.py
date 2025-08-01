"""
Application configuration management using Pydantic settings.

This module centralizes all environment-specific configuration,
making the application easy to deploy across different environments.
"""

from typing import List, Optional
from pydantic import BaseModel, validator
from pydantic_settings import BaseSettings
import json
import os


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    url: str = "sqlite:///./test.db"
    echo_sql: bool = False
    
    class Config:
        env_prefix = "DATABASE_"


class RedisSettings(BaseSettings):
    """Redis cache configuration settings."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    
    @property
    def url(self) -> str:
        """Construct Redis URL from individual components."""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"
    
    class Config:
        env_prefix = "REDIS_"


class ChromaSettings(BaseSettings):
    """ChromaDB vector database configuration."""
    host: str = "localhost"
    port: int = 8001
    fallback_host: str = "chroma"
    fallback_port: int = 8000
    collection_name: str = "rockwool_products"
    
    class Config:
        env_prefix = "CHROMA_"


class CelerySettings(BaseSettings):
    """Celery task queue configuration."""
    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/0"
    task_serializer: str = "json"
    accept_content: List[str] = ["json"]
    result_serializer: str = "json"
    timezone: str = "UTC"
    enable_utc: bool = True
    
    class Config:
        env_prefix = "CELERY_"


class CORSSettings(BaseSettings):
    """CORS (Cross-Origin Resource Sharing) configuration."""
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080"
    ]
    allow_credentials: bool = True
    allow_methods: List[str] = ["*"]
    allow_headers: List[str] = ["*"]
    
    @validator('allowed_origins', pre=True)
    def parse_origins(cls, v):
        """Parse comma-separated origins from environment variable."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    class Config:
        env_prefix = "CORS_"


class AIModelSettings(BaseSettings):
    """AI model configuration for document processing."""
    model_name: str = "claude-3-haiku-20240307"  # User requires Haiku 3.5
    provider: str = "anthropic"
    temperature: float = 0.0
    max_tokens: int = 8192
    min_tokens: int = 2048
    token_decrement: int = 1024
    max_retries: int = 3
    timeout_seconds: int = 30
    max_text_length: int = 8000
    max_tables_summary: int = 3
    
    class Config:
        env_prefix = "AI_"


class SecuritySettings(BaseSettings):
    """Security-related configuration."""
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_prefix = "SECURITY_"


class AnthropicSettings(BaseSettings):
    """Anthropic API configuration for Claude integration."""
    api_key: str = ""  # Must be set via ANTHROPIC_API_KEY environment variable
    
    class Config:
        env_prefix = "ANTHROPIC_"


class LoggingSettings(BaseSettings):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    class Config:
        env_prefix = "LOG_"


class AppSettings(BaseSettings):
    """Main application settings."""
    title: str = "Lambda.hu Építőanyag AI Rendszer"
    description: str = "AI-alapú építőanyag keresési és ajánlási rendszer"
    version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # Sub-configurations
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    chroma: ChromaSettings = ChromaSettings()
    celery: CelerySettings = CelerySettings()
    cors: CORSSettings = CORSSettings()
    ai: AIModelSettings = AIModelSettings()
    security: SecuritySettings = SecuritySettings()
    logging: LoggingSettings = LoggingSettings()
    anthropic: AnthropicSettings = AnthropicSettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load AI config from JSON file if it exists
        self._load_ai_config_from_file()
    
    def _load_ai_config_from_file(self):
        """Load AI configuration from JSON file if it exists."""
        config_path = os.path.join(
            os.path.dirname(__file__), 
            "ai_config.json"
        )
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    ai_config = json.load(f)
                
                # Update AI settings from JSON file
                model_config = ai_config.get("model", {})
                for key, value in model_config.items():
                    # Convert JSON keys to match Pydantic field names
                    if hasattr(self.ai, key):
                        setattr(self.ai, key, value)
                        
            except (json.JSONDecodeError, FileNotFoundError) as e:
                # Log error but continue with default values
                import logging
                logging.warning(f"Could not load AI config from file: {e}")
    
    @property
    def is_production(self) -> bool:
        """Check if application is running in production."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if application is running in development."""
        return self.environment.lower() == "development"
    
    @property
    def anthropic_api_key(self) -> str:
        """Get Anthropic API key with validation for production use."""
        if not self.anthropic.api_key:
            if self.is_production:
                raise ValueError(
                    "ANTHROPIC_API_KEY must be set in production environment. "
                    "No mock or placeholder keys allowed."
                )
            else:
                logging.warning("ANTHROPIC_API_KEY not set - AI features will be limited")
        return self.anthropic.api_key


# Create global settings instance
def get_settings() -> AppSettings:
    """Get application settings instance."""
    return AppSettings()


# Global settings instance - imported by other modules
settings = get_settings()