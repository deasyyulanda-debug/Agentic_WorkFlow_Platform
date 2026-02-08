"""
Application Configuration - Pydantic Settings Management
Loads config from environment variables with validation and defaults
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
import os

# Get the project root directory (parent of src/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Provides type safety and validation for configuration.
    """
    
    # API Configuration
    API_HOST: str = Field(default="0.0.0.0", description="API server host")
    API_PORT: int = Field(default=8000, description="API server port")
    API_RELOAD: bool = Field(default=True, description="Enable auto-reload (dev only)")
    API_WORKERS: int = Field(default=1, description="Number of worker processes")
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/db/workflows.db",
        description="Database connection URL"
    )
    DATABASE_ECHO: bool = Field(
        default=False,
        description="Echo SQL queries (dev only)"
    )
    
    # Security Configuration
    SECRET_KEY: str = Field(
        default="test-secret-key-min-32-chars-long-for-fernet-encryption",
        description="32-byte secret key for encryption (Fernet)"
    )
    
    # Artifacts Storage
    ARTIFACTS_PATH: str = Field(
        default="./data/artifacts",
        description="Path to artifacts storage"
    )
    
    # Provider API Keys (Optional - can be set via UI)
    OPENAI_API_KEY: Optional[str] = Field(
        default=None,
        description="OpenAI API key (optional)"
    )
    ANTHROPIC_API_KEY: Optional[str] = Field(
        default=None,
        description="Anthropic API key (optional)"
    )
    GOOGLE_API_KEY: Optional[str] = Field(
        default=None,
        description="Google Gemini API key (optional)"
    )
    DEEPSEEK_API_KEY: Optional[str] = Field(
        default=None,
        description="DeepSeek API key (optional)"
    )
    GROQ_API_KEY: Optional[str] = Field(
        default=None,
        description="Groq API key (optional)"
    )
    OPENROUTER_API_KEY: Optional[str] = Field(
        default=None,
        description="OpenRouter API key (optional)"
    )
    
    # Run Execution Limits (Test-Run Mode)
    TEST_RUN_MAX_TOKENS: int = Field(
        default=1000,
        description="Max tokens for test-run mode"
    )
    TEST_RUN_MAX_RUNTIME_SECONDS: int = Field(
        default=60,
        description="Max runtime for test-run mode"
    )
    TEST_RUN_MAX_ITERATIONS: int = Field(
        default=5,
        description="Max iterations for test-run mode"
    )
    
    # Application Metadata
    APP_NAME: str = Field(
        default="Agentic Workflow Platform",
        description="Application name"
    )
    APP_VERSION: str = Field(
        default="0.1.0",
        description="Application version"
    )
    
    # CORS Configuration
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins"
    )
    
    # Logging Configuration
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    LOG_FORMAT: str = Field(
        default="json",
        description="Log format (json or text)"
    )
    
    # Environment
    ENVIRONMENT: str = Field(
        default="development",
        description="Environment name (development, staging, production)"
    )
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(PROJECT_ROOT, ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra environment variables
    )
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT.lower() == "development"


# Global settings instance
# Loaded once at application startup
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings (singleton pattern).
    Loads from environment on first call, then caches.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Convenience export
settings = get_settings()
