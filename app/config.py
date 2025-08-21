# app/config.py
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_VERSION: str = os.getenv("API_VERSION", "v1")
    API_TITLE: str = "YouTube Data Pipeline API"
    
    # API Security
    API_KEY: str = os.getenv("API_KEY", "")

    # CORS Settings
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
    )
    CORS_ALLOW_CREDENTIALS: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    CORS_ALLOW_METHODS: str = os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,DELETE,OPTIONS")
    CORS_ALLOW_HEADERS: str = os.getenv("CORS_ALLOW_HEADERS", "Content-Type,Authorization,X-API-Key")

    @property
    def cors_origins_list(self) -> list[str]:
        """Restituisce la lista pulita e validata delle origini CORS ammesse"""
        origins = [self.FRONTEND_URL] + self.CORS_ORIGINS.split(",")
        # Filtra origini vuote e rimuove duplicati
        valid_origins = list({origin.strip() for origin in origins if origin.strip()})
        return valid_origins
    
    @property
    def cors_methods_list(self) -> list[str]:
        """Restituisce la lista dei metodi HTTP ammessi"""
        return [method.strip() for method in self.CORS_ALLOW_METHODS.split(",") if method.strip()]
    
    @property 
    def cors_headers_list(self) -> list[str]:
        """Restituisce la lista degli header ammessi"""
        return [header.strip() for header in self.CORS_ALLOW_HEADERS.split(",") if header.strip()]

    # Scraping Configuration
    USER_AGENT: str = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    )
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    PROXY_URL: Optional[str] = os.getenv("PROXY_URL") or None

    # Retry Configuration
    RETRY_ATTEMPTS: int = int(os.getenv("RETRY_ATTEMPTS", "3"))
    RETRY_WAIT_SECONDS: int = int(os.getenv("RETRY_WAIT_SECONDS", "2"))
    RETRY_BACKOFF_MULTIPLIER: float = float(os.getenv("RETRY_BACKOFF_MULTIPLIER", "1.5"))
    RETRY_MAX_WAIT_SECONDS: int = int(os.getenv("RETRY_MAX_WAIT_SECONDS", "10"))

    # Instagram Configuration
    INSTAGRAM_BASE_URL: str = os.getenv(
        "INSTAGRAM_BASE_URL", "https://www.instagram.com/"
    )

    # Crawlbase Configuration
    CRAWLBASE_NORMAL_TOKEN: str = os.getenv("CRAWLBASE_NORMAL_TOKEN", "")
    CRAWLBASE_JS_TOKEN: str = os.getenv("CRAWLBASE_JS_TOKEN", "")

    # Performance Settings
    PAGE_LOAD_TIMEOUT: int = int(os.getenv("PAGE_LOAD_TIMEOUT", "10000"))
    CONCURRENT_REQUESTS: int = int(os.getenv("CONCURRENT_REQUESTS", "5"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "detailed") 
    LOG_TO_FILE: bool = os.getenv("LOG_TO_FILE", "false").lower() == "true"
    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "logs/app.log")


settings = Settings()

# Validate configuration on import
if not settings.CRAWLBASE_NORMAL_TOKEN:
    raise ValueError("CRAWLBASE_NORMAL_TOKEN is required in .env file")
if not settings.CRAWLBASE_JS_TOKEN:
    raise ValueError("CRAWLBASE_JS_TOKEN is required in .env file")
if not settings.API_KEY:
    raise ValueError("API_KEY is required in .env file")
