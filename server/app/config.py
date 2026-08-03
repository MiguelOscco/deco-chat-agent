"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ============================================
    # APPLICATION
    # ============================================
    APP_NAME: str = "DECO Chat Agent"
    APP_VERSION: str = "0.3.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    WORKERS: int = int(os.getenv("WORKERS", 4))
    SERVER_ID: str = os.getenv("SERVER_ID", "server-1")
    
    # ============================================
    # SECURITY
    # ============================================
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-super-secret-key-change-in-production-at-least-32-chars")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Password hashing
    BCRYPT_ROUNDS: int = 12
    
    # ============================================
    # DATABASE
    # ============================================
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://deco:deco123@deco_postgres:5432/deco_db"
    )
    
    # ============================================
    # REDIS
    # ============================================
    REDIS_HOST: str = os.getenv("REDIS_HOST", "deco_redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # ============================================
    # GLPI
    # ============================================
    GLPI_BASE_URL: str = os.getenv(
        "GLPI_BASE_URL",
        "http://192.168.5.68/glpi/apirest.php"
    )
    GLPI_APP_TOKEN: str = os.getenv(
        "GLPI_APP_TOKEN",
        "hj77WbrOP3v2j4SmjxxjPGTVPoF1j4WZfxNCaybo"
    )
    GLPI_USER: str = os.getenv("GLPI_USER", "moscco")
    GLPI_PASSWORD: str = os.getenv("GLPI_PASSWORD", "Bysperu.com1")
    GLPI_TIMEOUT: int = 10
    
    # ============================================
    # OLLAMA / LLM
    # ============================================
    OLLAMA_BASE_URL: str = os.getenv(
        "OLLAMA_BASE_URL",
        "http://deco_ollama:11434"
    )
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "mistral")
    OLLAMA_TIMEOUT: int = 120
    OLLAMA_TEMPERATURE: float = 0.7
    
    # ============================================
    # LOGGING
    # ============================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "json"  # json or text
    LOG_FILE: str = os.getenv("LOG_FILE", "/var/log/deco-chat-agent/app.log")
    LOG_MAX_BYTES: int = 10_485_760  # 10 MB
    LOG_BACKUP_COUNT: int = 5
    
    # ============================================
    # CORS
    # ============================================
    CORS_ORIGINS: list = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://192.168.5.68",
        "http://192.168.5.68:9000",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    # ============================================
    # SECURITY HEADERS
    # ============================================
    ENABLE_HSTS: bool = True
    HSTS_MAX_AGE: int = 31536000  # 1 year
    ENABLE_CSP: bool = True
    ENABLE_NOSNIFF: bool = True
    ENABLE_XFRAME_OPTIONS: bool = True
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton instance
settings = Settings()
