from fastapi import APIRouter, HTTPException, status
from typing import Dict

from app.models.website import WebsiteRequest, WebsiteScrapingResult
from app.services.website import WebsiteScraper
from app.utils import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/scrape", tags=["Website Scraping"])


@router.post(
    "/website",
    response_model=WebsiteScrapingResult,
    status_code=status.HTTP_200_OK,
    summary="Scrape a website",
    description="Analyzes a website and extracts structured data including site structure, navigation, UX, and more"
)
async def scrape_website(request: WebsiteRequest) -> WebsiteScrapingResult:
    """
    Endpoint per lo scraping e l'analisi di un sito web.
    
    Parametri:
    - url: URL del sito web da analizzare
    
    Ritorna:
    - Dati strutturati del sito web secondo lo schema WebsiteScrapingResult
    """
    try:
        logger.info(f"Received scraping request for website: {request.url}")
        
        scraper = WebsiteScraper()
        result = await scraper.scrape(str(request.url))
        
        if result.error_message:
            logger.error(f"Scraping failed: {result.error_message}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to scrape website: {result.error_message}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in website scraping endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/website/health",
    response_model=Dict[str, str],
    summary="Health check for website scraper",
    description="Verifies that the website scraping service is operational"
)
async def website_health_check() -> Dict[str, str]:
    """
    Health check endpoint per il servizio di scraping website
    """
    return {
        "status": "healthy",
        "service": "website_scraper",
        "message": "Website scraping service is operational"
    }