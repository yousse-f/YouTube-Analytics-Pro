from .website_scraper import router as website_router
from .instagram_scraper import router as instagram_router
from .youtube_scraper import router as youtube_router

__all__ = ["website_router", "instagram_router", "youtube_router"]
