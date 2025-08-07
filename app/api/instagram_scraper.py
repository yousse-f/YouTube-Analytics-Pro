from fastapi import APIRouter, HTTPException, status
from typing import Dict

from app.models.instagram import InstagramRequest, InstagramScrapingResult
from app.services.instagram import InstagramScraper
from app.utils import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/scrape", tags=["Instagram Scraping"])


@router.post(
    "/instagram",
    response_model=InstagramScrapingResult,
    status_code=status.HTTP_200_OK,
    summary="Scrape an Instagram profile",
    description="Analyzes a public Instagram profile and extracts structured data including metrics, content analysis, and performance KPIs",
)
async def scrape_instagram(request: InstagramRequest) -> InstagramScrapingResult:
    """
    Endpoint per lo scraping e l'analisi di un profilo Instagram pubblico.

    Parametri:
    - username: Username del profilo Instagram da analizzare (senza @)

    Ritorna:
    - Dati strutturati del profilo Instagram secondo lo schema InstagramScrapingResult

    Note:
    - Funziona solo con profili pubblici
    - I dati attuali sono simulati per demo
    """
    try:
        # Validazione username
        username = request.username.strip().lstrip("@")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username cannot be empty",
            )

        if not username.replace("_", "").replace(".", "").isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Instagram username format",
            )

        logger.info(f"Received scraping request for Instagram: @{username}")

        scraper = InstagramScraper()
        result = await scraper.scrape(username)

        if result.error_message:
            logger.error(f"Scraping failed: {result.error_message}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to scrape Instagram profile: {result.error_message}",
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in Instagram scraping endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get(
    "/instagram/health",
    response_model=Dict[str, str],
    summary="Health check for Instagram scraper",
    description="Verifies that the Instagram scraping service is operational",
)
async def instagram_health_check() -> Dict[str, str]:
    """
    Health check endpoint per il servizio di scraping Instagram
    """
    return {
        "status": "healthy",
        "service": "instagram_scraper",
        "message": "Instagram scraping service is operational",
    }
