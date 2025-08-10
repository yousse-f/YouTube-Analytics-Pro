"""
Website Analyzer API - FastAPI Application.

Main application entry point with middleware, routing, and configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from app.config import settings
from app.api.website_analyzer import router as analyzer_router
from app.utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

# Application start time
start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(
        "Starting Website Analyzer API",
        extra={
            "version": "1.0.0",
            "api_version": settings.API_VERSION,
            "port": settings.API_PORT,
            "log_level": settings.LOG_LEVEL
        }
    )
    yield
    # Shutdown
    uptime = time.time() - start_time
    logger.info(
        "Shutting down Website Analyzer API",
        extra={"uptime_seconds": round(uptime, 2)}
    )


# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version="1.0.0",
    docs_url=f"/api/{settings.API_VERSION}/docs",
    redoc_url=f"/api/{settings.API_VERSION}/redoc",
    openapi_url=f"/api/{settings.API_VERSION}/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.cors_methods_list,
    allow_headers=settings.cors_headers_list,
)


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "detail": "The requested resource was not found",
            "timestamp": time.time()
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    logger.error(
        "Internal server error",
        extra={"error": str(exc), "path": str(request.url)},
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error", 
            "detail": "An unexpected error occurred",
            "timestamp": time.time()
        }
    )


# Include routers
app.include_router(
    analyzer_router,
    prefix=f"/api/{settings.API_VERSION}/website",
    tags=["Website Analysis"]
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information."""
    uptime = time.time() - start_time
    return {
        "service": "Website Analyzer API",
        "version": "1.0.0",
        "status": "operational",
        "uptime_seconds": round(uptime, 2),
        "docs_url": f"/api/{settings.API_VERSION}/docs",
        "api_version": settings.API_VERSION
    }


# Health check endpoint (public)
@app.get("/health")
async def health():
    """Simple health check endpoint."""
    return {"status": "healthy", "timestamp": time.time()}


if __name__ == "__main__":
    import uvicorn
    
    logger.info(
        "Starting development server",
        extra={"host": settings.API_HOST, "port": settings.API_PORT}
    )
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
