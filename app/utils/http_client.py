import httpx
from typing import Optional, Dict, Any
from app.config import Settings
from app.utils.logger import setup_logger
from app.utils.retry import retry_http_calls, with_retry_logging

logger = setup_logger(__name__)
settings = Settings()


class HTTPClient:
    """Client HTTP asincrono per scraping"""
    
    def __init__(self):
        self.headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        self.timeout = httpx.Timeout(settings.REQUEST_TIMEOUT)
        self.proxies = {"all://": settings.PROXY_URL} if settings.PROXY_URL else None
    
    @retry_http_calls
    @with_retry_logging
    async def get(
        self, 
        url: str, 
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True
    ) -> httpx.Response:
        """
        Esegue una richiesta GET asincrona con retry automatico
        """
        request_headers = {**self.headers}
        if headers:
            request_headers.update(headers)
        
        async with httpx.AsyncClient(
            timeout=self.timeout,
            proxies=self.proxies,
            follow_redirects=follow_redirects
        ) as client:
            try:
                logger.debug(
                    f"Making GET request to {url}",
                    extra={"url": url, "headers": request_headers}
                )
                response = await client.get(url, headers=request_headers)
                response.raise_for_status()
                logger.debug(
                    f"GET request successful",
                    extra={"url": url, "status_code": response.status_code}
                )
                return response
            except httpx.HTTPError as e:
                logger.warning(
                    f"HTTP error for {url}",
                    extra={"url": url, "error": str(e), "status_code": getattr(e.response, 'status_code', None)},
                    exc_info=True
                )
                raise
            except Exception as e:
                logger.error(
                    f"Unexpected error for {url}",
                    extra={"url": url, "error": str(e), "error_type": type(e).__name__},
                    exc_info=True
                )
                raise
    
    @retry_http_calls
    @with_retry_logging
    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        """
        Esegue una richiesta POST asincrona con retry automatico
        """
        request_headers = {**self.headers}
        if headers:
            request_headers.update(headers)
        
        async with httpx.AsyncClient(
            timeout=self.timeout,
            proxies=self.proxies
        ) as client:
            try:
                logger.debug(
                    f"Making POST request to {url}",
                    extra={"url": url, "has_data": data is not None, "has_json": json is not None}
                )
                response = await client.post(
                    url, 
                    data=data, 
                    json=json, 
                    headers=request_headers
                )
                response.raise_for_status()
                logger.debug(
                    f"POST request successful",
                    extra={"url": url, "status_code": response.status_code}
                )
                return response
            except httpx.HTTPError as e:
                logger.warning(
                    f"HTTP error for {url}",
                    extra={"url": url, "error": str(e), "status_code": getattr(e.response, 'status_code', None)},
                    exc_info=True
                )
                raise
            except Exception as e:
                logger.error(
                    f"Unexpected error for {url}",
                    extra={"url": url, "error": str(e), "error_type": type(e).__name__},
                    exc_info=True
                )
                raise