"""
Gestione Configurazione per Website Analyzer API.

Configurazione centralizzata usando Pydantic Settings con variabili d'ambiente.
Ottimizzata per performance e sicurezza in produzione.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """
    Configurazioni dell'applicazione con supporto variabili d'ambiente.
    
    Centralizza tutte le configurazioni per maggiore sicurezza e facilità
    di deployment in ambienti diversi (dev, staging, production).
    """
    
    # Configurazione API Core
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8003
    API_VERSION: str = "v1"
    API_TITLE: str = "Website Analyzer API"
    API_DESCRIPTION: str = "Microservizio per analisi completa di siti web e business intelligence"
    
    # Sicurezza e Autenticazione
    API_KEY: str  # Obbligatorio - deve essere impostato nel .env
    
    # Configurazione CORS (ottimizzata per sicurezza)
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:8003"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = "GET,POST,PUT,DELETE,OPTIONS,HEAD"
    CORS_ALLOW_HEADERS: str = "Content-Type,Authorization,X-API-Key,Accept,Origin"
    
    # Configurazione Analisi Siti Web (ottimizzata per performance)
    USER_AGENT: str = "WebsiteAnalyzer/1.0 (Business Intelligence Bot; +https://studioinnovativo.it)"
    REQUEST_TIMEOUT: int = 30
    MAX_PAGE_SIZE: int = 10485760  # 10MB - limite sicurezza
    FOLLOW_REDIRECTS: bool = True
    MAX_REDIRECTS: int = 5  # Nuovo: limite redirect per sicurezza
    
    # Configurazione Retry (ottimizzata per resilienza)
    RETRY_ATTEMPTS: int = 3
    RETRY_WAIT_SECONDS: int = 2
    RETRY_BACKOFF_MULTIPLIER: float = 1.5
    RETRY_MAX_WAIT_SECONDS: int = 10
    
    # Impostazioni Analisi (ottimizzate per qualità risultati)
    MAX_PAGES_TO_ANALYZE: int = 5
    ANALYSIS_DEPTH: str = "standard"  # basic | standard | comprehensive | enterprise
    INCLUDE_SUBDOMAINS: bool = False
    CONTENT_LANGUAGE_DETECTION: bool = True  # Nuovo: rilevamento automatico lingua
    EXTRACT_SOCIAL_MEDIA: bool = True  # Nuovo: estrazione link social media
    
    # Configurazione Logging (strutturato per production)
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "detailed"  # detailed | json
    LOG_TO_FILE: bool = False
    LOG_FILE_PATH: str = "logs/website-analyzer.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def cors_methods_list(self) -> List[str]:
        """Convert CORS_ALLOW_METHODS string to list."""
        return [method.strip() for method in self.CORS_ALLOW_METHODS.split(",")]
    
    @property
    def cors_headers_list(self) -> List[str]:
        """Convert CORS_ALLOW_HEADERS string to list."""
        return [header.strip() for header in self.CORS_ALLOW_HEADERS.split(",")]
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    @field_validator("ANALYSIS_DEPTH")
    @classmethod
    def validate_analysis_depth(cls, v):
        """Validate analysis depth."""
        valid_depths = ["basic", "standard", "comprehensive"]
        if v.lower() not in valid_depths:
            raise ValueError(f"ANALYSIS_DEPTH must be one of {valid_depths}")
        return v.lower()


# Global settings instance
settings = Settings()
