import logging
import logging.config
import os
import sys
from datetime import datetime
from pathlib import Path
from app.core.config import settings

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)


def setup_logging():
    """Configure logging for the application."""
    
    # Check if logging is already configured
    if logging.getLogger().handlers:
        return logging.getLogger(__name__)
    
    # Logging configuration
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "api": {
                "format": "%(asctime)s - API - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "default",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG" if settings.debug else "INFO",
                "formatter": "detailed",
                "filename": logs_dir / "app.log",
                "maxBytes": 10 * 1024 * 1024,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
            "api_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "api",
                "filename": logs_dir / "api.log",
                "maxBytes": 10 * 1024 * 1024,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": logs_dir / "errors.log",
                "maxBytes": 10 * 1024 * 1024,  # 10MB
                "backupCount": 10,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "": {  # Root logger
                "level": "DEBUG" if settings.debug else "INFO",
                "handlers": ["console", "file", "error_file"],
            },
            "api": {  # API requests logger
                "level": "INFO",
                "handlers": ["api_file"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "error_file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["api_file"],
                "propagate": False,
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "motor": {
                "level": "WARNING",
                "handlers": ["file"],
                "propagate": False,
            },
            "apscheduler": {
                "level": "INFO",
                "handlers": ["file"],
                "propagate": False,
            },
        },
    }
    
    # Apply logging configuration
    logging.config.dictConfig(logging_config)
    
    # Set up logger for this module
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)


class StructuredLogger:
    """Structured logger for better log analysis."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration: float,
        user_id: str = None,
        ip_address: str = None,
    ):
        """Log API request with structured data."""
        extra_data = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration": duration,
            "user_id": user_id,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        message = f"{method} {path} - {status_code} - {duration:.3f}s"
        if user_id:
            message += f" - User: {user_id}"
        
        self.logger.info(message, extra=extra_data)
    
    def log_ai_usage(
        self,
        provider: str,
        operation: str,
        tokens_used: int = None,
        cost: float = None,
        duration: float = None,
        success: bool = True,
    ):
        """Log AI service usage."""
        extra_data = {
            "provider": provider,
            "operation": operation,
            "tokens_used": tokens_used,
            "cost": cost,
            "duration": duration,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        message = f"AI {provider} - {operation}"
        if tokens_used:
            message += f" - {tokens_used} tokens"
        if duration:
            message += f" - {duration:.3f}s"
        
        level = logging.INFO if success else logging.ERROR
        self.logger.log(level, message, extra=extra_data)
    
    def log_file_processing(
        self,
        filename: str,
        file_size: int,
        processing_type: str,
        duration: float = None,
        success: bool = True,
        error: str = None,
    ):
        """Log file processing events."""
        extra_data = {
            "filename": filename,
            "file_size": file_size,
            "processing_type": processing_type,
            "duration": duration,
            "success": success,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        message = f"File processing - {processing_type} - {filename} ({file_size} bytes)"
        if duration:
            message += f" - {duration:.3f}s"
        
        if success:
            self.logger.info(message, extra=extra_data)
        else:
            self.logger.error(f"{message} - Error: {error}", extra=extra_data)


# Initialize logging on module import (only if not already initialized)
if not logging.getLogger().handlers:
    setup_logging()
