"""
Structured logging configuration.

Provides:
- JSON structured logging
- Request/response logging
- Sensitive data masking
- Performance metrics
- Log rotation
"""


import logging
import logging.handlers
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
import os

from config import settings

# ============================================
# SENSITIVE DATA MASKING
# ============================================

SENSITIVE_FIELDS = {
    "password", "secret", "token", "api_key", "authorization",
    "glpi_password", "glpi_app_token", "db_password",
    "redis_password", "jwt_secret"
}

def mask_sensitive_data(data: Any, depth: int = 0, max_depth: int = 10) -> Any:
    """Recursively mask sensitive fields in data structures."""
    if depth > max_depth:
        return data
    
    if isinstance(data, dict):
        return {
            key: "***REDACTED***" if key.lower() in SENSITIVE_FIELDS 
            else mask_sensitive_data(value, depth + 1, max_depth)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [mask_sensitive_data(item, depth + 1, max_depth) for item in data]
    elif isinstance(data, str) and len(data) > 100:
        return data[:50] + f"...({len(data)} chars)"
    
    return data

# ============================================
# JSON FORMATTER
# ============================================

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
            "server_id": settings.SERVER_ID or "unknown"
        }
        
        if hasattr(record, "extra_fields"):
            log_data.update(mask_sensitive_data(record.extra_fields))
        
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        return json.dumps(log_data, default=str)

# ============================================
# LOGGER SETUP
# ============================================

def setup_logging() -> None:
    """Configure application logging."""
    
    logs_dir = "/app/logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.LOG_LEVEL)
    
    if settings.DEBUG:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
    else:
        formatter = JSONFormatter()
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    file_handler = logging.handlers.RotatingFileHandler(
        filename=f"{logs_dir}/app.log",
        maxBytes=10485760,
        backupCount=10,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    error_handler = logging.handlers.RotatingFileHandler(
        filename=f"{logs_dir}/error.log",
        maxBytes=10485760,
        backupCount=5,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(error_handler)
    
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)

def get_logger(name: str):
    """Get a logger with context support."""
    logger = logging.getLogger(name)
    return LoggerAdapter(logger)

# ============================================
# LOGGER ADAPTER
# ============================================

class LoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter for adding context."""
    
    def process(self, msg: str, kwargs: Dict) -> tuple:
        """Add context to log messages."""
        return msg, kwargs
    
    def with_context(self, **context):
        """Add context fields to logger."""
        new_adapter = LoggerAdapter(self.logger, self.extra.copy())
        new_adapter.extra.update(context)
        return new_adapter
    
    def info(self, msg: str, *args, **kwargs):
        """Log info with context."""
        self.logger.info(msg, *args, extra={"extra_fields": self.extra}, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """Log warning with context."""
        self.logger.warning(msg, *args, extra={"extra_fields": self.extra}, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """Log error with context."""
        self.logger.error(msg, *args, extra={"extra_fields": self.extra}, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs):
        """Log debug with context."""
        self.logger.debug(msg, *args, extra={"extra_fields": self.extra}, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        """Log critical with context."""
        self.logger.critical(msg, *args, extra={"extra_fields": self.extra}, **kwargs) 
