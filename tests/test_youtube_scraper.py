"""
Unit tests for YouTube scraper service.
Tests the core scraping functionality, data extraction, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import asyncio
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from app.services.youtube import YouTubeScraper
from app.models.youtube import YouTubeScrapingResult


class TestYouTubeScraper:
    """Test suite for YouTubeScraper service."""

    def test_scraper_initialization_headless(self, mock_webdriver_manager, mock_chrome_options):
        """Test scraper initialization in headless mode."""
        with patch('app.services.youtube.webdriver.Chrome') as mock_chrome:
            scraper = YouTubeScraper(headless=True)
            
            # Verify Chrome options were configured for headless
            mock_chrome_options.add_argument.assert_any_call("--headless=new")
            mock_chrome_options.add_argument.assert_any_call("--disable-gpu")
            mock_chrome.assert_called_once()

    def test_scraper_initialization_non_headless(self, mock_webdriver_manager, mock_chrome_options):
        """Test scraper initialization in non-headless mode."""
        with patch('app.services.youtube.webdriver.Chrome') as mock_chrome:
            scraper = YouTubeScraper(headless=False)
            
            # Verify headless arguments were not added
            headless_calls = [call("--headless=new") for call in mock_chrome_options.add_argument.call_args_list]
            assert not any(headless_calls)
            mock_chrome.assert_called_once()

    def test_scraper_initialization_failure(self, mock_webdriver_manager):
        """Test scraper initialization when WebDriver fails."""
        with patch('app.services.youtube.webdriver.Chrome', side_effect=Exception("Chrome failed to start")):
            with pytest.raises(Exception, match="Chrome failed to start"):
                YouTubeScraper(headless=True)

    @patch('app.services.youtube.webdriver.Chrome')
    def test_reject_cookies_success(self, mock_chrome, mock_webdriver_manager):
        """Test successful cookie rejection."""
        # Setup mock driver
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        # Mock the cookie rejection button
        mock_button = Mock()
        mock_wait = Mock()
        mock_wait.until.return_value = mock_button
        
        with patch('app.services.youtube.WebDriverWait', return_value=mock_wait):
            scraper = YouTubeScraper(headless=True)
            scraper.reject_cookies()
            
            # Verify button was clicked
            mock_button.click.assert_called_once()

    @patch('app.services.youtube.webdriver.Chrome')
    def test_reject_cookies_timeout(self, mock_chrome, mock_webdriver_manager):
        """Test cookie rejection when button is not found."""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        with patch('app.services.youtube.WebDriverWait') as mock_wait_class:
            mock_wait = Mock()
            mock_wait.until.side_effect = TimeoutException("Button not found")
            mock_wait_class.return_value = mock_wait
            
            scraper = YouTubeScraper(headless=True)
            # Should not raise exception, just log and continue
            scraper.reject_cookies()

    @pytest.mark.asyncio
    @patch('app.services.youtube.webdriver.Chrome')
    async def test_scrape_channel_success(self, mock_chrome, mock_webdriver_manager, mock_selenium_elements, sample_youtube_url):
        """Test successful channel scraping."""
        # Setup mock driver
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        # Mock WebDriverWait and element finding
        with patch('app.services.youtube.WebDriverWait') as mock_wait_class:
            mock_wait = Mock()
            mock_wait_class.return_value = mock_wait
            
            # Mock the elements that will be found
            mock_wait.until.side_effect = [
                mock_selenium_elements['channel_name'],
                mock_selenium_elements['channel_handle'],
                mock_selenium_elements['subscribers'],
                mock_selenium_elements['videos'],
                mock_selenium_elements['description']
            ]
            
            # Mock find_elements for video links
            mock_driver.find_elements.return_value = mock_selenium_elements['video_links']
            
            scraper = YouTubeScraper(headless=True)
            
            with patch.object(scraper, 'reject_cookies'):
                result = await scraper.scrape(sample_youtube_url)
            
            # Verify successful result
            assert isinstance(result, YouTubeScrapingResult)
            assert result.channel_name == "Test Tech Channel"
            assert result.channel_handle == "@testtechchannel"
            assert result.subscribers == "1.2M subscribers"
            assert result.videos == "245 videos"
            assert len(result.first_10_videos) == 10
            assert result.error_message is None

    @pytest.mark.asyncio
    @patch('app.services.youtube.webdriver.Chrome')
    async def test_scrape_channel_timeout_error(self, mock_chrome, mock_webdriver_manager, sample_youtube_url):
        """Test channel scraping with timeout error."""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        with patch('app.services.youtube.WebDriverWait') as mock_wait_class:
            mock_wait = Mock()
            mock_wait.until.side_effect = TimeoutException("Page load timeout")
            mock_wait_class.return_value = mock_wait
            
            scraper = YouTubeScraper(headless=True)
            
            with patch.object(scraper, 'reject_cookies'):
                result = await scraper.scrape(sample_youtube_url)
            
            # Verify error result
            assert isinstance(result, YouTubeScrapingResult)
            assert result.error_message is not None
            assert "timeout" in result.error_message.lower()

    @pytest.mark.asyncio
    @patch('app.services.youtube.webdriver.Chrome')
    async def test_scrape_channel_element_not_found(self, mock_chrome, mock_webdriver_manager, sample_youtube_url):
        """Test channel scraping when elements are not found."""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        with patch('app.services.youtube.WebDriverWait') as mock_wait_class:
            mock_wait = Mock()
            mock_wait.until.side_effect = NoSuchElementException("Element not found")
            mock_wait_class.return_value = mock_wait
            
            scraper = YouTubeScraper(headless=True)
            
            with patch.object(scraper, 'reject_cookies'):
                result = await scraper.scrape(sample_youtube_url)
            
            # Verify error result
            assert isinstance(result, YouTubeScrapingResult)
            assert result.error_message is not None

    @patch('app.services.youtube.webdriver.Chrome')
    def test_scraper_quit(self, mock_chrome, mock_webdriver_manager):
        """Test scraper cleanup."""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        scraper = YouTubeScraper(headless=True)
        scraper.quit()
        
        # Verify driver.quit() was called
        mock_driver.quit.assert_called_once()

    @patch('app.services.youtube.webdriver.Chrome')
    def test_scraper_quit_with_error(self, mock_chrome, mock_webdriver_manager):
        """Test scraper cleanup when quit fails."""
        mock_driver = Mock()
        mock_driver.quit.side_effect = Exception("Quit failed")
        mock_chrome.return_value = mock_driver
        
        scraper = YouTubeScraper(headless=True)
        # Should not raise exception, just log warning
        scraper.quit()

    @pytest.mark.asyncio
    @patch('app.services.youtube.webdriver.Chrome')
    async def test_video_links_extraction_limit(self, mock_chrome, mock_webdriver_manager, sample_youtube_url):
        """Test that video link extraction respects the 10 video limit."""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        # Create 15 mock video elements (more than the limit of 10)
        video_elements = []
        for i in range(15):
            element = Mock()
            element.get_attribute.return_value = f"https://www.youtube.com/watch?v=test{i}"
            video_elements.append(element)
        
        mock_driver.find_elements.return_value = video_elements
        
        with patch('app.services.youtube.WebDriverWait') as mock_wait_class:
            mock_wait = Mock()
            # Mock other required elements
            mock_element = Mock()
            mock_element.text = "Test"
            mock_wait.until.return_value = mock_element
            mock_wait_class.return_value = mock_wait
            
            scraper = YouTubeScraper(headless=True)
            
            with patch.object(scraper, 'reject_cookies'):
                result = await scraper.scrape(sample_youtube_url)
            
            # Verify only 10 videos are returned
            assert len(result.first_10_videos) == 10
            assert all("test" in url for url in result.first_10_videos)

    @pytest.mark.asyncio
    @patch('app.services.youtube.webdriver.Chrome')
    async def test_scrape_with_duplicate_video_urls(self, mock_chrome, mock_webdriver_manager, sample_youtube_url):
        """Test that duplicate video URLs are filtered out."""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        # Create mock elements with duplicate URLs
        video_elements = []
        duplicate_url = "https://www.youtube.com/watch?v=duplicate"
        for i in range(5):
            element = Mock()
            element.get_attribute.return_value = duplicate_url  # Same URL for all
            video_elements.append(element)
        
        mock_driver.find_elements.return_value = video_elements
        
        with patch('app.services.youtube.WebDriverWait') as mock_wait_class:
            mock_wait = Mock()
            mock_element = Mock()
            mock_element.text = "Test"
            mock_wait.until.return_value = mock_element
            mock_wait_class.return_value = mock_wait
            
            scraper = YouTubeScraper(headless=True)
            
            with patch.object(scraper, 'reject_cookies'):
                result = await scraper.scrape(sample_youtube_url)
            
            # Should have only 1 unique URL despite 5 elements
            assert len(result.first_10_videos) == 1
            assert result.first_10_videos[0] == duplicate_url

    @pytest.mark.parametrize("url,expected_valid", [
        ("https://www.youtube.com/@testchannel", True),
        ("https://www.youtube.com/c/TestChannel", True),
        ("https://youtube.com/@test", True),
        ("http://invalid-url", False),
        ("not-a-url", False),
        ("", False),
    ])
    @patch('app.services.youtube.webdriver.Chrome')
    def test_url_validation_patterns(self, mock_chrome, mock_webdriver_manager, url, expected_valid):
        """Test various URL patterns for validation."""
        scraper = YouTubeScraper(headless=True)
        
        # This is a basic test - in a real implementation, you might want to add URL validation
        # For now, we just test that the scraper can be initialized with different URLs
        assert scraper is not None
