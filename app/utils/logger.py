"""
Centralized Logging Module

Provides consistent logging configuration across the microservice.
All logging should go through this module to ensure consistency.
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional
from app.config import settings


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Configura e restituisce un logger con formato standardizzato
    
    Args:
        name: Nome del logger (solitamente __name__)
        level: Livello di logging opzionale (usa settings.LOG_LEVEL se None)
    
    Returns:
        Logger configurato e pronto all'uso
    """
    logger = logging.getLogger(name)
    
    # Use provided level or fall back to settings
    log_level = level or settings.LOG_LEVEL
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    if settings.LOG_FORMAT == "json":
        # JSON format for production/structured logging
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # Human readable format for development
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler (always present)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if settings.LOG_TO_FILE:
        # Create logs directory if it doesn't exist
        log_file = Path(settings.LOG_FILE_PATH)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Ottiene un logger già configurato o ne crea uno nuovo
    
    Args:
        name: Nome del logger
        
    Returns:
        Logger configurato
    """
    return setup_logger(name)