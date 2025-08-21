# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.config import settings
from app.api import website_router, instagram_router, youtube_router
from app.utils import setup_logger

logger = setup_logger(__name__)

# Crea l'applicazione FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    description="Advanced YouTube Data Pipeline - Professional scraping and analysis API for channel insights, video metadata extraction, and AI-ready datasets",
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurazione CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.cors_methods_list,
    allow_headers=settings.cors_headers_list,
)

# Include routers
app.include_router(website_router, prefix=f"/api/{settings.API_VERSION}")
app.include_router(instagram_router, prefix=f"/api/{settings.API_VERSION}")
app.include_router(youtube_router, prefix=f"/api/{settings.API_VERSION}")


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - verifica che l'API sia attiva
    """
    return {
        "message": "YouTube Data Pipeline API",
        "version": settings.API_VERSION,
        "description": "Advanced YouTube scraping and analysis service",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "youtube_scraping": "/api/v1/scrape/youtube",
            "health_check": "/health"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check generale dell'applicazione
    """
    return {
        "status": "healthy",
        "service": "scs-data-management",
        "version": settings.API_VERSION,
        "endpoints": {
            "website_scraper": "/api/v1/scrape/website",
            "instagram_scraper": "/api/v1/scrape/instagram",
            "youtube_scraper": f"/api/{settings.API_VERSION}/scrape/youtube",
        },
    }


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """
    Handler personalizzato per errori 404
    """
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested URL {request.url.path} was not found",
            "docs": "/docs",
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """
    Handler personalizzato per errori 500
    """
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


@app.on_event("startup")
async def startup_event():
    """
    Eventi da eseguire all'avvio dell'applicazione
    """
    logger.info(
        f"Starting {settings.API_TITLE} on {settings.API_HOST}:{settings.API_PORT}"
    )
    logger.info(f"API Version: {settings.API_VERSION}")
    logger.info(f"CORS enabled for origins: {settings.cors_origins_list}")
    logger.info(f"CORS methods allowed: {settings.cors_methods_list}")
    logger.info(f"CORS headers allowed: {settings.cors_headers_list}")
    logger.info("API documentation available at /docs")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Eventi da eseguire allo shutdown dell'applicazione
    """
    logger.info("Shutting down application")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
