from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict
from app.models.youtube import YouTubeRequest, YouTubeScrapingResult
from app.services.youtube import YouTubeScraper
from app.utils.logger import setup_logger
from app.security.api_key import verify_api_key

logger = setup_logger(__name__)

router = APIRouter(prefix="/scrape", tags=["YouTube Scraping"])


@router.post(
    "/youtube",
    response_model=YouTubeScrapingResult,
    status_code=status.HTTP_200_OK,
    summary="Scrape a YouTube channel",
    description="Analizza un canale YouTube pubblico e restituisce i dati principali",
    dependencies=[Depends(verify_api_key)]
)
async def scrape_youtube(request: YouTubeRequest) -> YouTubeScrapingResult:
    """
    Endpoint per lo scraping di un canale YouTube pubblico.
    """
    try:
        target_url = request.url.strip()
        if not target_url:
            logger.warning("YouTube scraping request with empty URL")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="YouTube URL cannot be empty",
            )

        logger.info("Starting YouTube scraping request for URL: %s", target_url)

        scraper = YouTubeScraper(headless=True)
        result = await scraper.scrape(target_url)
        scraper.quit()

        if result.error_message:
            logger.error("YouTube scraping failed for URL %s: %s", target_url, result.error_message)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to scrape YouTube: {result.error_message}",
            )

        logger.info("YouTube scraping completed successfully for URL: %s (channel: %s)", 
                   target_url, result.channel_name)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in YouTube scraping endpoint for URL %s: %s", 
                    getattr(request, 'url', 'unknown'), str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get(
    "/youtube/health",
    response_model=Dict[str, str],
    summary="Health check for YouTube scraper",
    description="Verifica che il servizio di scraping YouTube sia operativo",
)
async def youtube_health_check() -> Dict[str, str]:
    """
    Health check endpoint per il servizio di scraping YouTube.
    """
    logger.debug("YouTube health check requested")
    return {
        "status": "healthy",
        "service": "youtube_scraper",
        "message": "YouTube scraping service is operational",
    }
