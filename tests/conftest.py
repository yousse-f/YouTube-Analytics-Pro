"""
Test configuration and fixtures for YouTube Data Pipeline.
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.models.youtube import YouTubeScrapingResult


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def async_client():
    """Create an async test client."""
    return AsyncClient(app=app, base_url="http://test")


@pytest.fixture
def valid_api_key():
    """Return a valid API key for testing."""
    return "test-api-key-123"


@pytest.fixture
def invalid_api_key():
    """Return an invalid API key for testing."""
    return "invalid-key"


@pytest.fixture
def sample_youtube_url():
    """Sample YouTube channel URL for testing."""
    return "https://www.youtube.com/@testchannel"


@pytest.fixture
def mock_youtube_result():
    """Mock successful YouTube scraping result."""
    return YouTubeScrapingResult(
        channel_name="Test Tech Channel",
        channel_handle="@testtechchannel",
        subscribers="1.2M subscribers",
        videos="245 videos",
        description="Welcome to our test tech channel where we explore the latest in technology and innovation.",
        first_10_videos=[
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=oHg5SJYRHA0",
            "https://www.youtube.com/watch?v=J5hVWIc1w4Y",
            "https://www.youtube.com/watch?v=8ybW48rKBME",
            "https://www.youtube.com/watch?v=QH2-TGUlwu4"
        ]
    )


@pytest.fixture
def mock_youtube_error_result():
    """Mock failed YouTube scraping result."""
    return YouTubeScrapingResult(
        channel_name="",
        channel_handle="",
        subscribers="",
        videos="",
        description="",
        first_10_videos=[],
        error_message="Failed to load channel: Timeout waiting for page elements"
    )


@pytest.fixture
def mock_webdriver():
    """Mock Selenium WebDriver for testing."""
    driver_mock = Mock()
    driver_mock.get = Mock()
    driver_mock.find_element = Mock()
    driver_mock.find_elements = Mock(return_value=[])
    driver_mock.quit = Mock()
    driver_mock.page_source = "<html><body>Test Page</body></html>"
    return driver_mock


@pytest.fixture
def mock_webdriver_manager():
    """Mock WebDriverManager for testing."""
    with patch('app.services.youtube.ChromeDriverManager') as mock_manager:
        mock_manager.return_value.install.return_value = "/fake/chromedriver/path"
        yield mock_manager


@pytest.fixture
def mock_selenium_elements():
    """Mock Selenium WebElements for testing."""
    channel_name_element = Mock()
    channel_name_element.text = "Test Tech Channel"
    
    channel_handle_element = Mock()
    channel_handle_element.text = "@testtechchannel"
    
    subscribers_element = Mock()
    subscribers_element.text = "1.2M subscribers"
    
    videos_element = Mock()
    videos_element.text = "245 videos"
    
    description_element = Mock()
    description_element.text = "Welcome to our test tech channel"
    
    video_links = []
    for i in range(10):
        link_element = Mock()
        link_element.get_attribute.return_value = f"https://www.youtube.com/watch?v=test{i}"
        video_links.append(link_element)
    
    return {
        'channel_name': channel_name_element,
        'channel_handle': channel_handle_element,
        'subscribers': subscribers_element,
        'videos': videos_element,
        'description': description_element,
        'video_links': video_links
    }


@pytest.fixture
def mock_chrome_options():
    """Mock Chrome options for testing."""
    with patch('app.services.youtube.webdriver.ChromeOptions') as mock_options:
        mock_instance = Mock()
        mock_options.return_value = mock_instance
        yield mock_instance


# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Environment patches
@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("API_KEY", "test-api-key-123")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("PAGE_LOAD_TIMEOUT", "5000")
    monkeypatch.setenv("REQUEST_TIMEOUT", "10")
    monkeypatch.setenv("RETRY_ATTEMPTS", "2")
    monkeypatch.setenv("API_TITLE", "YouTube Data Pipeline API - Test")
    return monkeypatch
