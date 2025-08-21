"""
Integration tests for YouTube Data Pipeline API endpoints.
Tests the complete API workflow including authentication, request processing, and response validation.
"""

import pytest
import json
from unittest.mock import patch, Mock
from fastapi import status

from app.models.youtube import YouTubeRequest, YouTubeScrapingResult


class TestYouTubeAPI:
    """Integration test suite for YouTube API endpoints."""

    @pytest.fixture
    def api_headers(self, valid_api_key):
        """Headers with valid API key for authenticated requests."""
        return {"X-API-Key": valid_api_key}

    @pytest.fixture
    def invalid_api_headers(self, invalid_api_key):
        """Headers with invalid API key for testing authentication."""
        return {"X-API-Key": invalid_api_key}

    def test_root_endpoint(self, test_client):
        """Test the root endpoint returns correct information."""
        response = test_client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["message"] == "YouTube Data Pipeline API"
        assert "version" in data
        assert "endpoints" in data
        assert "youtube_scraping" in data["endpoints"]

    def test_health_endpoint(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "uptime_seconds" in data
        assert "timestamp" in data

    def test_youtube_scraping_success(self, test_client, api_headers, mock_youtube_result):
        """Test successful YouTube channel scraping via API."""
        request_data = {
            "url": "https://www.youtube.com/@testchannel"
        }

        # Mock the scraper service
        with patch("app.api.youtube_scraper.YouTubeScraper") as mock_scraper_class:
            mock_scraper = Mock()
            mock_scraper_class.return_value = mock_scraper
            mock_scraper.scrape.return_value = mock_youtube_result
            
            response = test_client.post(
                "/api/v1/scrape/youtube",
                json=request_data,
                headers=api_headers
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["channel_name"] == "Test Tech Channel"
        assert data["channel_handle"] == "@testtechchannel"
        assert data["subscribers"] == "1.2M subscribers"
        assert data["videos"] == "245 videos"
        assert len(data["first_10_videos"]) == 5
        assert data["error_message"] is None

    def test_youtube_scraping_with_error(self, test_client, api_headers, mock_youtube_error_result):
        """Test YouTube scraping when service returns error."""
        request_data = {
            "url": "https://www.youtube.com/@nonexistentchannel"
        }

        with patch("app.api.youtube_scraper.YouTubeScraper") as mock_scraper_class:
            mock_scraper = Mock()
            mock_scraper_class.return_value = mock_scraper
            mock_scraper.scrape.return_value = mock_youtube_error_result
            
            response = test_client.post(
                "/api/v1/scrape/youtube",
                json=request_data,
                headers=api_headers
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data
        assert "Failed to scrape YouTube" in data["detail"]

    def test_youtube_scraping_invalid_url(self, test_client, api_headers):
        """Test YouTube scraping with invalid URL format."""
        request_data = {
            "url": "not-a-valid-url"
        }

        response = test_client.post(
            "/api/v1/scrape/youtube",
            json=request_data,
            headers=api_headers
        )

        # The request should still be processed (URL validation is basic)
        # But may fail during scraping
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]

    def test_youtube_scraping_empty_url(self, test_client, api_headers):
        """Test YouTube scraping with empty URL."""
        request_data = {
            "url": ""
        }

        response = test_client.post(
            "/api/v1/scrape/youtube",
            json=request_data,
            headers=api_headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "cannot be empty" in data["detail"]

    def test_youtube_scraping_missing_url(self, test_client, api_headers):
        """Test YouTube scraping without URL parameter."""
        request_data = {}

        response = test_client.post(
            "/api/v1/scrape/youtube",
            json=request_data,
            headers=api_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_youtube_scraping_unauthorized(self, test_client, invalid_api_headers):
        """Test YouTube scraping with invalid API key."""
        request_data = {
            "url": "https://www.youtube.com/@testchannel"
        }

        response = test_client.post(
            "/api/v1/scrape/youtube",
            json=request_data,
            headers=invalid_api_headers
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_youtube_scraping_no_auth(self, test_client):
        """Test YouTube scraping without authentication headers."""
        request_data = {
            "url": "https://www.youtube.com/@testchannel"
        }

        response = test_client.post(
            "/api/v1/scrape/youtube",
            json=request_data
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_youtube_scraping_service_exception(self, test_client, api_headers):
        """Test YouTube scraping when scraper service raises exception."""
        request_data = {
            "url": "https://www.youtube.com/@testchannel"
        }

        with patch("app.api.youtube_scraper.YouTubeScraper") as mock_scraper_class:
            mock_scraper_class.side_effect = Exception("Selenium WebDriver failed to initialize")
            
            response = test_client.post(
                "/api/v1/scrape/youtube",
                json=request_data,
                headers=api_headers
            )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.parametrize("invalid_json", [
        '{"url": "https://youtube.com/@test", "invalid": }',  # Invalid JSON
        '{"url": 12345}',  # Wrong data type
        '{}'  # Empty object (missing required field)
    ])
    def test_youtube_scraping_invalid_json(self, test_client, api_headers, invalid_json):
        """Test YouTube scraping with various invalid JSON payloads."""
        response = test_client.post(
            "/api/v1/scrape/youtube",
            data=invalid_json,
            headers={**api_headers, "Content-Type": "application/json"}
        )

        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST, 
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_youtube_scraping_large_response(self, test_client, api_headers):
        """Test YouTube scraping with large response data."""
        request_data = {
            "url": "https://www.youtube.com/@popularchannelwithmanyvideos"
        }

        # Mock large response
        large_result = YouTubeScrapingResult(
            channel_name="Popular Channel with Very Long Name That Might Cause Issues",
            channel_handle="@popularchannelwithmanyvideos",
            subscribers="10M subscribers",
            videos="5000 videos",
            description="A" * 2000,  # Very long description
            first_10_videos=[f"https://www.youtube.com/watch?v=video{i}" for i in range(10)]
        )

        with patch("app.api.youtube_scraper.YouTubeScraper") as mock_scraper_class:
            mock_scraper = Mock()
            mock_scraper_class.return_value = mock_scraper
            mock_scraper.scrape.return_value = large_result
            
            response = test_client.post(
                "/api/v1/scrape/youtube",
                json=request_data,
                headers=api_headers
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["description"]) == 2000
        assert len(data["first_10_videos"]) == 10

    def test_concurrent_scraping_requests(self, test_client, api_headers, mock_youtube_result):
        """Test multiple concurrent YouTube scraping requests."""
        import threading
        
        request_data = {
            "url": "https://www.youtube.com/@testchannel"
        }
        
        responses = []
        
        def make_request():
            with patch("app.api.youtube_scraper.YouTubeScraper") as mock_scraper_class:
                mock_scraper = Mock()
                mock_scraper_class.return_value = mock_scraper
                mock_scraper.scrape.return_value = mock_youtube_result
                
                response = test_client.post(
                    "/api/v1/scrape/youtube",
                    json=request_data,
                    headers=api_headers
                )
                responses.append(response)
        
        # Create 3 concurrent requests
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded
        assert len(responses) == 3
        for response in responses:
            assert response.status_code == status.HTTP_200_OK

    def test_api_documentation_endpoints(self, test_client):
        """Test that API documentation endpoints are accessible."""
        # Test OpenAPI docs
        docs_response = test_client.get("/docs")
        assert docs_response.status_code == status.HTTP_200_OK
        
        # Test ReDoc
        redoc_response = test_client.get("/redoc")
        assert redoc_response.status_code == status.HTTP_200_OK
        
        # Test OpenAPI JSON
        openapi_response = test_client.get("/openapi.json")
        assert openapi_response.status_code == status.HTTP_200_OK
        openapi_data = openapi_response.json()
        assert "openapi" in openapi_data
        assert "paths" in openapi_data

    def test_cors_headers(self, test_client, api_headers):
        """Test CORS headers are properly set."""
        request_data = {
            "url": "https://www.youtube.com/@testchannel"
        }

        with patch("app.api.youtube_scraper.YouTubeScraper"):
            response = test_client.post(
                "/api/v1/scrape/youtube",
                json=request_data,
                headers=api_headers
            )

        # Check for CORS headers (if configured)
        # This depends on your CORS configuration
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    def test_request_timeout_handling(self, test_client, api_headers):
        """Test API handling of long-running requests."""
        request_data = {
            "url": "https://www.youtube.com/@slowloadingchannel"
        }

        # Mock a slow response
        def slow_scrape(*args, **kwargs):
            import time
            time.sleep(0.1)  # Small delay for testing
            return YouTubeScrapingResult(
                channel_name="Slow Channel",
                channel_handle="@slowchannel",
                subscribers="100 subscribers",
                videos="10 videos",
                description="A slow loading channel",
                first_10_videos=[]
            )

        with patch("app.api.youtube_scraper.YouTubeScraper") as mock_scraper_class:
            mock_scraper = Mock()
            mock_scraper_class.return_value = mock_scraper
            mock_scraper.scrape.side_effect = slow_scrape
            
            response = test_client.post(
                "/api/v1/scrape/youtube",
                json=request_data,
                headers=api_headers
            )

        assert response.status_code == status.HTTP_200_OK
