from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

from app.models.youtube import YouTubeScrapingResult
from app.utils.logger import setup_logger
from app.utils.retry import retry_selenium_operations, with_retry_logging

logger = setup_logger(__name__)


class YouTubeScraper:
    def __init__(self, headless: bool = True):
        """
        Inizializza il scraper YouTube con Selenium
        
        Args:
            headless: Se True, esegue Chrome in modalità headless
        """
        logger.info("Initializing YouTube scraper (headless=%s)", headless)
        
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
        
        # Disable Chrome logging
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument("--log-level=3")
        options.add_argument("--disable-logging")
        
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()), options=options
            )
            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Chrome WebDriver: %s", str(e), exc_info=True)
            raise

    def reject_cookies(self):
        """Rifiuta i cookie su YouTube"""
        try:
            logger.debug("Attempting to reject YouTube cookies")
            reject_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        '//yt-button-shape/button[@aria-label[contains(.,"Reject")]]',
                    )
                )
            )
            self.driver.execute_script("arguments[0].click();", reject_button)
            logger.info("Successfully rejected YouTube cookies")
        except Exception as e:
            logger.warning("Could not reject cookies (continuing anyway): %s", str(e))

    @retry_selenium_operations
    @with_retry_logging
    async def scrape(self, url: str) -> YouTubeScrapingResult:
        """
        Esegue lo scraping di un canale YouTube con retry automatico
        
        Args:
            url: URL del canale YouTube da analizzare
            
        Returns:
            Risultato dello scraping con dati del canale
        """
        logger.info(
            "Starting YouTube scraping for URL",
            extra={"url": url, "retry_enabled": True}
        )
        
        try:
            # Navigate to YouTube and handle cookies
            logger.debug("Navigating to YouTube homepage")
            self.driver.get("https://www.youtube.com/")
            self.reject_cookies()
            
            # Navigate to target channel
            logger.debug("Navigating to channel URL", extra={"url": url})
            self.driver.get(url)

            # Extract channel data with improved error handling
            logger.debug("Extracting channel name")
            channel_name = (
                WebDriverWait(self.driver, 10)
                .until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            '//h1[contains(@class,"dynamic-text-view-model-wiz")]/span',
                        )
                    )
                )
                .text
            )
            logger.info("Found channel name", extra={"channel_name": channel_name})

            logger.debug("Extracting channel handle")
            channel_handle = (
                WebDriverWait(self.driver, 10)
                .until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            '(//yt-content-metadata-view-model//span[@role="text"])[1]',
                        )
                    )
                )
                .text
            )

            logger.debug("Extracting subscriber count")
            subscribers = (
                WebDriverWait(self.driver, 10)
                .until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            '(//yt-content-metadata-view-model//span[@role="text"])[2]',
                        )
                    )
                )
                .text
            )

            logger.debug("Extracting video count")
            videos = (
                WebDriverWait(self.driver, 10)
                .until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            '(//yt-content-metadata-view-model//span[@role="text"])[3]',
                        )
                    )
                )
                .text
            )

            logger.debug("Extracting channel description")
            description = (
                WebDriverWait(self.driver, 10)
                .until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            '//yt-description-preview-view-model//span[@role="text" and not(ancestor::button)]',
                        )
                    )
                )
                .text
            )

            # Extract video links
            logger.debug("Extracting video links")
            elements = self.driver.find_elements(By.TAG_NAME, "a")
            video_links = []
            for elem in elements:
                href = elem.get_attribute("href")
                if href and "watch?v=" in href and href not in video_links:
                    video_links.append(href)
                if len(video_links) == 10:
                    break
            
            logger.info("Successfully scraped channel: %s (%d videos found)", 
                       channel_name, len(video_links))

            return YouTubeScrapingResult(
                channel_name=channel_name,
                channel_handle=channel_handle,
                subscribers=subscribers,
                videos=videos,
                description=description,
                first_10_videos=video_links,
            )

        except Exception as e:
            logger.error("YouTube scraping failed for URL %s: %s", url, str(e), exc_info=True)
            return YouTubeScrapingResult(
                channel_name="",
                channel_handle="",
                subscribers="",
                videos="",
                description="",
                first_10_videos=[],
                error_message=str(e),
            )

    def quit(self):
        """Chiude il browser e rilascia le risorse"""
        try:
            logger.debug("Closing Chrome WebDriver")
            self.driver.quit()
            logger.info("Chrome WebDriver closed successfully")
        except Exception as e:
            logger.warning("Error closing WebDriver: %s", str(e))
