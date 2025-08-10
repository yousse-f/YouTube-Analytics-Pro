"""
HTTP client for Website Analyzer API.

Provides resilient HTTP client with retry mechanism and error handling.
"""

import httpx
from typing import Optional, Dict, Any
from app.config import settings
from app.utils.logger import setup_logger
from app.utils.retry import retry_http_calls, with_retry_logging

logger = setup_logger(__name__)


class WebsiteHTTPClient:
    """HTTP client for website analysis with retry capabilities."""
    
    def __init__(self):
        """Initialize HTTP client with default configuration."""
        self.headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        self.timeout = httpx.Timeout(settings.REQUEST_TIMEOUT)
        self.limits = httpx.Limits(
            max_connections=10,
            max_keepalive_connections=5
        )
    
    @retry_http_calls
    @with_retry_logging
    async def get(
        self, 
        url: str, 
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = None
    ) -> httpx.Response:
        """
        Execute GET request with retry mechanism.
        
        Args:
            url: Target URL
            headers: Additional headers
            follow_redirects: Whether to follow redirects
            
        Returns:
            HTTP response
            
        Raises:
            httpx.HTTPStatusError: For HTTP errors
            httpx.RequestError: For connection errors
        """
        request_headers = {**self.headers}
        if headers:
            request_headers.update(headers)
        
        follow_redirects = follow_redirects if follow_redirects is not None else settings.FOLLOW_REDIRECTS
        
        async with httpx.AsyncClient(
            timeout=self.timeout,
            limits=self.limits,
            follow_redirects=follow_redirects
        ) as client:
            try:
                logger.debug(
                    f"Making GET request",
                    extra={
                        "url": url, 
                        "follow_redirects": follow_redirects,
                        "timeout": settings.REQUEST_TIMEOUT
                    }
                )
                
                response = await client.get(url, headers=request_headers)
                
                # Check content length
                content_length = len(response.content)
                if content_length > settings.MAX_PAGE_SIZE:
                    logger.warning(
                        f"Page size exceeds maximum allowed",
                        extra={
                            "url": url,
                            "content_length": content_length,
                            "max_allowed": settings.MAX_PAGE_SIZE
                        }
                    )
                
                response.raise_for_status()
                
                logger.debug(
                    f"GET request successful",
                    extra={
                        "url": url, 
                        "status_code": response.status_code,
                        "content_length": content_length,
                        "content_type": response.headers.get("content-type", "unknown")
                    }
                )
                
                return response
                
            except httpx.HTTPStatusError as e:
                logger.warning(
                    f"HTTP error",
                    extra={
                        "url": url, 
                        "status_code": e.response.status_code,
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
            except httpx.RequestError as e:
                logger.error(
                    f"Request error",
                    extra={
                        "url": url, 
                        "error": str(e), 
                        "error_type": type(e).__name__
                    },
                    exc_info=True
                )
                raise
            except Exception as e:
                logger.error(
                    f"Unexpected error",
                    extra={
                        "url": url, 
                        "error": str(e), 
                        "error_type": type(e).__name__
                    },
                    exc_info=True
                )
                raise
    
    async def head(self, url: str) -> httpx.Response:
        """
        Execute HEAD request to check URL availability.
        
        Args:
            url: Target URL
            
        Returns:
            HTTP response (headers only)
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.head(url, headers=self.headers)
                response.raise_for_status()
                return response
            except Exception as e:
                logger.debug(
                    f"HEAD request failed",
                    extra={"url": url, "error": str(e)}
                )
                raise
