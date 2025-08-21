"""
Performance testing configuration for YouTube Analytics Pro API.
Load testing with realistic YouTube analytics scenarios.
"""

from locust import HttpUser, task, between, events
import json
import logging

# Configure logging for Locust
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YouTubeAPIUser(HttpUser):
    """
    Load testing user for YouTube Data Pipeline API.
    Simulates realistic usage patterns of the scraping service.
    """
    
    wait_time = between(2, 8)  # Wait 2-8 seconds between requests (realistic scraping interval)
    
    def on_start(self):
        """Called when a simulated user starts."""
        self.headers = {
            "X-API-Key": "test-performance-key",
            "Content-Type": "application/json"
        }
        
        # Sample YouTube channels for testing
        self.test_channels = [
            "https://www.youtube.com/@mkbhd",
            "https://www.youtube.com/@veritasium",
            "https://www.youtube.com/@3blue1brown",
            "https://www.youtube.com/@kurzgesagt",
            "https://www.youtube.com/@techcrunch"
        ]
        self.channel_index = 0
    
    @task(5)
    def health_check(self):
        """Test the health check endpoint (frequent, lightweight)."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed with status {response.status_code}")
    
    @task(3)
    def root_endpoint(self):
        """Test the root endpoint (moderate frequency)."""
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Root endpoint failed with status {response.status_code}")
    
    @task(1)
    def scrape_youtube_channel(self):
        """
        Test the main YouTube scraping endpoint.
        This is the heavy operation we want to test under load.
        """
        # Rotate through test channels
        channel_url = self.test_channels[self.channel_index % len(self.test_channels)]
        self.channel_index += 1
        
        payload = {
            "url": channel_url
        }
        
        with self.client.post(
            "/api/v1/scrape/youtube",
            json=payload,
            headers=self.headers,
            catch_response=True,
            timeout=60  # Allow more time for scraping operations
        ) as response:
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Validate response structure
                    required_fields = ["channel_name", "channel_handle", "subscribers", "videos"]
                    if all(field in data for field in required_fields):
                        response.success()
                        logger.info(f"Successfully scraped: {data.get('channel_name', 'Unknown')}")
                    else:
                        response.failure("Response missing required fields")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
                    
            elif response.status_code == 422:
                # Unprocessable entity - scraping failed but API worked
                logger.warning(f"Scraping failed for {channel_url}: {response.text}")
                response.success()  # Don't count as failure since API responded correctly
                
            elif response.status_code == 401:
                response.failure("Authentication failed")
                
            elif response.status_code == 500:
                response.failure("Internal server error")
                
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(1)
    def scrape_invalid_url(self):
        """Test API handling of invalid URLs (error scenarios)."""
        invalid_urls = [
            "https://www.youtube.com/@nonexistentchannel12345",
            "https://invalid-url",
            "not-a-url-at-all"
        ]
        
        invalid_url = invalid_urls[self.channel_index % len(invalid_urls)]
        
        payload = {"url": invalid_url}
        
        with self.client.post(
            "/api/v1/scrape/youtube",
            json=payload,
            headers=self.headers,
            catch_response=True,
            timeout=30
        ) as response:
            
            if response.status_code in [422, 400]:
                # Expected error responses
                response.success()
            elif response.status_code == 200:
                # Sometimes invalid URLs might still return data (or empty results)
                response.success()
            else:
                response.failure(f"Unexpected error handling: {response.status_code}")


class YouTubeAPIAdminUser(HttpUser):
    """
    Administrative user for testing monitoring endpoints.
    Simulates monitoring/health check systems.
    """
    
    wait_time = between(5, 15)  # Less frequent monitoring checks
    
    def on_start(self):
        """Initialize admin user."""
        self.headers = {
            "X-API-Key": "test-admin-key",
            "Content-Type": "application/json"
        }
    
    @task(10)
    def health_monitoring(self):
        """Frequent health check monitoring."""
        self.client.get("/health")
    
    @task(2)
    def api_documentation(self):
        """Access API documentation."""
        self.client.get("/docs")
        self.client.get("/openapi.json")


# Custom event handlers for detailed reporting
@events.request.add_listener
def record_youtube_scraping_metrics(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """Custom event handler to track YouTube scraping specific metrics."""
    if name == "/api/v1/scrape/youtube" and response and response.status_code == 200:
        try:
            data = response.json()
            video_count = len(data.get("first_10_videos", []))
            logger.info(f"Scraped {video_count} videos in {response_time}ms for {data.get('channel_name', 'Unknown')}")
        except:
            pass


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Event handler for test start."""
    logger.info("🚀 Starting YouTube Data Pipeline load testing...")
    logger.info(f"Target host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Event handler for test completion."""
    logger.info("✅ YouTube Data Pipeline load testing completed!")
    
    # Print summary statistics
    stats = environment.stats
    logger.info(f"📊 Total requests: {stats.total.num_requests}")
    logger.info(f"📊 Failed requests: {stats.total.num_failures}")
    logger.info(f"📊 Average response time: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"📊 Max response time: {stats.total.max_response_time:.2f}ms")


# Performance test scenarios
class LightLoadUser(HttpUser):
    """Light load testing - primarily health checks and basic endpoints."""
    weight = 3
    wait_time = between(1, 3)
    
    def on_start(self):
        self.headers = {"X-API-Key": "test-light-key"}
    
    @task
    def light_operations(self):
        self.client.get("/health")


class HeavyLoadUser(HttpUser):
    """Heavy load testing - YouTube scraping operations."""
    weight = 1
    wait_time = between(10, 20)  # Longer waits for heavy operations
    
    def on_start(self):
        self.headers = {
            "X-API-Key": "test-heavy-key",
            "Content-Type": "application/json"
        }
    
    @task
    def heavy_scraping(self):
        payload = {"url": "https://www.youtube.com/@testchannel"}
        self.client.post("/api/v1/scrape/youtube", json=payload, headers=self.headers)
