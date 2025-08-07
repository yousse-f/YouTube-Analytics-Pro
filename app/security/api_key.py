"""
API Key Security Module

Provides API Key authentication for protecting endpoints.
"""

from fastapi import HTTPException, Header
from typing import Annotated

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def verify_api_key(x_api_key: Annotated[str, Header(description="API Key for authentication")]) -> None:
    """
    Verify API Key from request header.
    
    Args:
        x_api_key: API Key from X-API-Key header
        
    Raises:
        HTTPException: 401 if API Key is invalid or missing
    """
    if not x_api_key:
        logger.warning("API Key authentication failed: Missing API Key")
        raise HTTPException(
            status_code=401,
            detail="Missing API Key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    if x_api_key != settings.API_KEY:
        logger.warning(f"API Key authentication failed: Invalid API Key provided")
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    logger.debug("API Key authentication successful")
