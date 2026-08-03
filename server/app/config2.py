"""
Application configuration and settings management.

This module centralizes all environment variables and configuration
using Pydantic for type safety and validation.
"""


from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Uses Pydantic v2 BaseSettings for automatic validation and type conversion.
    All sensitive values are hidden in logs.
    """
    
    # ============================================
    # APPLICATION
    # ============================================
    APP_NAME: str = Field(default="DECO Chat Agent", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    ENVIRONMENT: str = Field(default="development", description="Environment (development/staging/production)")
    DEBUG: bool = Field(default=False, description="Debug mode flag")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # ============================================
    # SECURITY
    # ============================================
    JWT_SECRET: str = Field(..., description="JWT signing secret key")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRATION_HOURS: int = Field(default=8, description="JWT token expiration in hours")
    
    # Password settings
    PASSWORD_MIN_LENGTH: int = Field(default=8, description="Minimum password length")
    PASSWORD_REQUIRE_UPPERCASE: bool = Field(default=True, description="Require uppercase in password")
    PASSWORD_REQUIRE_DIGITS: bool = Field(default=True, description="Require digits in password")
    PASSWORD_REQUIRE_SPECIAL: bool = Field(default=True, description="Require special chars in password")
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Requests per minute")
    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=60, description="Rate limit window in seconds")
    
    # CORS
    CORS_ORIGINS: list = Field(default=["*"], description="CORS allowed origins")
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="Allow credentials in CORS")
    CORS_ALLOW_METHODS: list = Field(default=["GET", "POST", "PUT", "DELETE"], description="Allowed HTTP methods")
    
    # ============================================
    # GLPI INTEGRATION
    # ============================================
    GLPI_URL: str = Field(..., description="GLPI API base URL")
    GLPI_APP_TOKEN: str = Field(..., description="GLPI API app token")
    GLPI_USER: str = Field(..., description="GLPI username")
    GLPI_PASSWORD: str = Field(..., description="GLPI password")
    GLPI_TIMEOUT: int = Field(default=10, description="GLPI request timeout in seconds")
    GLPI_RETRY_ATTEMPTS: int = Field(default=3, description="GLPI retry attempts")
    
    # ============================================
    # DATABASE
    # ============================================
    DB_HOST: str = Field(default="localhost", description="Database host")
    DB_PORT: int = Field(default=5432, description="Database port")
    DB_NAME: str = Field(..., description="Database name")
    DB_USER: str = Field(..., description="Database user")
    DB_PASSWORD: str = Field(..., description="Database password")
    DB_POOL_SIZE: int = Field(default=20, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=10, description="Database max overflow connections")
    DB_ECHO: bool = Field(default=False, description="Echo SQL queries in logs")
    
    # ============================================
    # REDIS
    # ============================================
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    REDIS_SOCKET_TIMEOUT: int = Field(default=5, description="Redis socket timeout")
    REDIS_SOCKET_CONNECT_TIMEOUT: int = Field(default=5, description="Redis connect timeout")
    
    # ============================================
    # OLLAMA (LLM)
    # ============================================
    OLLAMA_HOST: str = Field(default="localhost", description="Ollama host")
    OLLAMA_PORT: int = Field(default=11434, description="Ollama port")
    OLLAMA_MODEL: str = Field(default="mistral", description="Ollama model name")
    OLLAMA_TIMEOUT: int = Field(default=120, description="Ollama request timeout in seconds")
    OLLAMA_TEMPERATURE: float = Field(default=0.3, description="LLM temperature (0-1)")
    
    # ============================================
    # FASTAPI
    # ============================================
    WORKERS: int = Field(default=4, description="Number of Uvicorn workers")
    PORT: int = Field(default=8000, description="Application port")
    HOST: str = Field(default="0.0.0.0", description="Application host")
    
    # ============================================
    # SERVER IDENTIFICATION
    # ============================================
    SERVER_ID: Optional[int] = Field(default=None, description="Server instance ID")
    
    # ============================================
    # VALIDATORS
    # ============================================
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Validate environment is one of allowed values."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v
    
    @validator("JWT_SECRET")
    def validate_jwt_secret(cls, v):
        """Validate JWT secret is secure."""
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return v
    
    @validator("PASSWORD_MIN_LENGTH")
    def validate_password_min_length(cls, v):
        """Validate minimum password length."""
        if v < 8:
            raise ValueError("PASSWORD_MIN_LENGTH must be at least 8")
        return v
    
    @validator("RATE_LIMIT_REQUESTS")
    def validate_rate_limit(cls, v):
        """Validate rate limit requests."""
        if v < 1:
            raise ValueError("RATE_LIMIT_REQUESTS must be positive")
        return v
    
    # ============================================
    # DATABASE CONNECTION STRING
    # ============================================
    @property
    def DATABASE_URL(self) -> str:
        """Construct PostgreSQL connection URL."""
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    
    @property
    def REDIS_URL(self) -> str:
        """Construct Redis connection URL."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def OLLAMA_BASE_URL(self) -> str:
        """Construct Ollama base URL."""
        return f"http://{self.OLLAMA_HOST}:{self.OLLAMA_PORT}"
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
