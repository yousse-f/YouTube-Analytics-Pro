#!/usr/bin/env python3
"""
Test script per dimostrare il sistema di logging centralizzato
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from app.utils.logger import setup_logger

def test_logging_levels():
    """Test dei diversi livelli di logging"""
    logger = setup_logger("test.levels")
    
    print("🧪 Testing logging levels...")
    logger.debug("This is a DEBUG message (might not appear depending on LOG_LEVEL)")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    
    # Test exception logging
    try:
        raise ValueError("Test exception for logging")
    except Exception as e:
        logger.error("Caught exception: %s", str(e), exc_info=True)

def test_structured_logging():
    """Test del logging strutturato con parametri"""
    logger = setup_logger("test.structured")
    
    print("\n🏗️  Testing structured logging...")
    
    # Good practices
    user_id = "user_123"
    operation = "youtube_scrape"
    url = "https://youtube.com/@test"
    
    logger.info("Starting operation: %s for user: %s", operation, user_id)
    logger.info("Processing URL: %s", url)
    logger.warning("Rate limit approaching for user: %s", user_id)
    logger.error("Operation failed: %s (user: %s, url: %s)", operation, user_id, url)

def test_different_modules():
    """Test di logger per moduli diversi"""
    print("\n📦 Testing different module loggers...")
    
    api_logger = setup_logger("api.youtube")
    service_logger = setup_logger("service.scraper")
    utils_logger = setup_logger("utils.browser")
    
    api_logger.info("API request received")
    service_logger.info("Starting scraping process")
    utils_logger.debug("Browser initialized")
    utils_logger.info("Navigation completed")
    service_logger.info("Scraping completed successfully")
    api_logger.info("Response sent to client")

def main():
    """Test principale del sistema di logging"""
    print("🔍 TESTING CENTRALIZED LOGGING SYSTEM")
    print("=" * 50)
    
    # Show current configuration
    from app.config import settings
    print(f"LOG_LEVEL: {settings.LOG_LEVEL}")
    print(f"LOG_FORMAT: {settings.LOG_FORMAT}")
    print(f"LOG_TO_FILE: {settings.LOG_TO_FILE}")
    if settings.LOG_TO_FILE:
        print(f"LOG_FILE_PATH: {settings.LOG_FILE_PATH}")
    
    print()
    
    test_logging_levels()
    test_structured_logging() 
    test_different_modules()
    
    print("\n✅ Logging tests completed!")
    
    if settings.LOG_TO_FILE and Path(settings.LOG_FILE_PATH).exists():
        print(f"\n📁 Check log file: {settings.LOG_FILE_PATH}")

if __name__ == "__main__":
    main()
