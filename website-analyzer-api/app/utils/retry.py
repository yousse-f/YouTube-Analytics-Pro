"""
Retry utilities for external calls in Website Analyzer API.

Provides decorators and functions for implementing retry logic 
with exponential backoff for resilient external service calls.
"""

import functools
import logging
from typing import Type, Union, Tuple

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
)
import httpx
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def create_retry_decorator(
    exception_types: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    stop_attempts: int = None,
    wait_seconds: int = None,
    backoff_multiplier: float = None,
    max_wait_seconds: int = None,
):
    """
    Create a retry decorator with configurable parameters.
    
    Args:
        exception_types: Exception types to retry on
        stop_attempts: Maximum number of retry attempts
        wait_seconds: Initial wait time between retries
        backoff_multiplier: Exponential backoff multiplier
        max_wait_seconds: Maximum wait time between retries
    
    Returns:
        Configured retry decorator
    """
    # Use settings defaults if not provided
    stop_attempts = stop_attempts or settings.RETRY_ATTEMPTS
    wait_seconds = wait_seconds or settings.RETRY_WAIT_SECONDS
    backoff_multiplier = backoff_multiplier or settings.RETRY_BACKOFF_MULTIPLIER
    max_wait_seconds = max_wait_seconds or settings.RETRY_MAX_WAIT_SECONDS
    
    return retry(
        stop=stop_after_attempt(stop_attempts),
        wait=wait_exponential(
            multiplier=backoff_multiplier,
            min=wait_seconds,
            max=max_wait_seconds
        ),
        retry=retry_if_exception_type(exception_types),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
        reraise=True,
    )


# Pre-configured retry decorators for common scenarios

# HTTP/API calls (httpx, connection errors)
retry_http_calls = create_retry_decorator(
    exception_types=(
        httpx.RequestError,
        httpx.ConnectError,
        httpx.TimeoutException,
        httpx.HTTPStatusError,
        ConnectionError,
        TimeoutError,
    )
)

# General external service calls
retry_external_calls = create_retry_decorator(
    exception_types=(
        ConnectionError,
        TimeoutError,
        httpx.RequestError,
        Exception,  # Include general Exception for testing and unexpected errors
    )
)


def with_retry_logging(func):
    """
    Decorator to add structured logging around retry operations.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(
            f"Starting operation with retry",
            extra={
                "function": func.__name__,
                "retry_config": {
                    "max_attempts": settings.RETRY_ATTEMPTS,
                    "wait_seconds": settings.RETRY_WAIT_SECONDS,
                    "backoff_multiplier": settings.RETRY_BACKOFF_MULTIPLIER,
                    "max_wait_seconds": settings.RETRY_MAX_WAIT_SECONDS,
                }
            }
        )
        
        try:
            result = func(*args, **kwargs)
            logger.info(
                f"Operation completed successfully",
                extra={"function": func.__name__}
            )
            return result
        except Exception as e:
            logger.error(
                f"Operation failed after all retries",
                extra={
                    "function": func.__name__,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True
            )
            raise
    
    return wrapper
