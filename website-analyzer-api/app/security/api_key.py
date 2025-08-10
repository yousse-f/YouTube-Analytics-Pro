"""
API Key authentication for Website Analyzer API.

Provides FastAPI dependency for API key validation and security.
"""

from fastapi import HTTPException, Header, status
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def verify_api_key(api_key: str = Header(alias="X-API-Key")) -> str:
    """
    Verify API key from X-API-Key header.
    
    Args:
        api_key: API key from request header
        
    Returns:
        Validated API key
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not api_key:
        logger.warning(
            "API key authentication failed: missing key",
            extra={"reason": "missing_api_key"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include X-API-Key header in your request.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if api_key != settings.API_KEY:
        logger.warning(
            "API key authentication failed: invalid key",
            extra={"reason": "invalid_api_key", "provided_key_prefix": api_key[:8] + "..."}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key. Please check your X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    logger.info(
        "API key authentication successful",
        extra={"api_key_prefix": api_key[:8] + "..."}
    )
    
    return api_key
