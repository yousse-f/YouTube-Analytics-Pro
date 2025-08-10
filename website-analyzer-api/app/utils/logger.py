"""
Centralized logging system for Website Analyzer API.

Provides structured logging with configurable formats and levels.
"""

import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from app.config import settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class DetailedFormatter(logging.Formatter):
    """Detailed human-readable formatter."""
    
    def __init__(self):
        super().__init__(
            fmt="[%(asctime)s] [%(levelname)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def setup_logger(name: str) -> logging.Logger:
    """
    Set up a logger with configured formatting and handlers.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Set log level
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Choose formatter
    if settings.LOG_FORMAT.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = DetailedFormatter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if settings.LOG_TO_FILE:
        log_file_path = Path(settings.LOG_FILE_PATH)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def log_extra(**kwargs) -> Dict[str, Any]:
    """
    Create extra data for structured logging.
    
    Usage:
        logger.info("User action", extra=log_extra(user_id=123, action="login"))
    """
    return {"extra": kwargs}
