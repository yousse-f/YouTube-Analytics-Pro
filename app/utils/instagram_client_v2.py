"""
Instagram Client V2 - Clean implementation using CrawlbaseParser

Provides a clean interface for Instagram data scraping with:
- Dual scraper approach (profile + posts)
- Proper data parsing with field corrections
- Engagement rate calculations
- Error handling and retries
"""

import time
import asyncio
from typing import Dict, List, Any, Optional
from crawlbase import CrawlingAPI
from app.config import settings
from app.utils.logger import setup_logger
from app.utils.crawlbase_parser import CrawlbaseParser

logger = setup_logger(__name__)


class InstagramClientV2:
    """Clean Instagram client using dedicated parser"""
    
    def __init__(self):
        """Initialize client with Crawlbase API and parser"""
        self.api = CrawlingAPI({'token': settings.CRAWLBASE_JS_TOKEN})  # Use JS token for Instagram
        self.parser = CrawlbaseParser()
        self.timeout = 120000  # 2 minutes
        logger.info("InstagramClientV2 initialized with JS token successfully")
    
    def _make_api_request(self, url: str, scraper: str, retry_count: int = 2) -> Dict[str, Any]:
        """
        Make API request with retry logic
        
        Args:
            url: Instagram URL to scrape
            scraper: Scraper type ('instagram-profile' or 'instagram-post')
            retry_count: Number of retries on failure
            
        Returns:
            Raw API response
            
        Raises:
            Exception: If all retries fail
        """
        last_error = None
        
        for attempt in range(retry_count + 1):
            try:
                response = self.api.get(url, {
                    'scraper': scraper,
                    'format': 'json',
                    'timeout': self.timeout
                })
                
                if response.get('status_code') == 200:
                    return response
                else:
                    error_msg = f"API returned status {response.get('status_code', 'unknown')}"
                    logger.warning(f"{error_msg}. Response: {response}")
                    last_error = Exception(error_msg)
                    
            except Exception as e:
                logger.warning(f"Connection error: {str(e)}. Retrying...")
                last_error = e
            
            if attempt < retry_count:
                wait_time = (attempt + 1) * 1.0
                logger.info(f"Retry attempt {attempt + 1}/{retry_count} after {wait_time}s")
                time.sleep(wait_time)
        
        raise last_error or Exception("API request failed")
    
    def get_profile_data(self, username: str) -> Dict[str, Any]:
        """
        Get Instagram profile data
        
        Args:
            username: Instagram username (without @)
            
        Returns:
            Parsed profile data dictionary
        """
        url = f"https://www.instagram.com/{username}/"
        logger.info(f"Fetching profile data for @{username}")
        
        try:
            # Make API request
            response = self._make_api_request(url, 'instagram-profile')
            
            # Extract body from response
            body = self.parser.extract_response_body(response)
            
            # Parse profile data
            profile = self.parser.parse_profile_data(body)
            
            # Get post URLs from profile response
            posts_preview = self.parser.parse_profile_posts(body)
            
            logger.info(f"Successfully scraped profile @{username}: {profile.followers_count} followers")
            
            return {
                'username': profile.username,
                'name': profile.name,
                'verified': profile.verified,
                'followers': profile.followers_count,
                'following': profile.following_count,
                'total_posts': profile.posts_count,
                'biography': profile.bio,
                'profile_pic_url': profile.profile_pic_url,
                'is_business': profile.is_business,
                'external_url': profile.external_url,
                'posts_preview': posts_preview
            }
            
        except Exception as e:
            logger.error(f"Failed to get profile data for @{username}: {str(e)}")
            raise
    
    def get_profile_posts_urls(self, username: str) -> List[str]:
        """
        Get post URLs from profile
        
        Args:
            username: Instagram username
            
        Returns:
            List of post URLs
        """
        try:
            profile_data = self.get_profile_data(username)
            posts_preview = profile_data.get('posts_preview', [])
            
            urls = [post['link'] for post in posts_preview if post.get('link')]
            logger.info(f"Found {len(urls)} post URLs for @{username}")
            
            return urls
            
        except Exception as e:
            logger.error(f"Failed to get post URLs for @{username}: {str(e)}")
            return []
    
    def get_post_details(self, post_url: str) -> Dict[str, Any]:
        """
        Get detailed post data
        
        Args:
            post_url: Instagram post URL
            
        Returns:
            Parsed post data dictionary
        """
        # Reduced logging for production
        
        try:
            # Make API request
            response = self._make_api_request(post_url, 'instagram-post')
            
            # Extract body
            body = self.parser.extract_response_body(response)
            
            # Parse post data
            post = self.parser.parse_post_data(body)
            
            return {
                'shortcode': post.shortcode,
                'likesCount': post.likes_count,
                'commentsCount': post.comments_count,
                'caption': post.caption,
                'timestamp': post.timestamp,
                'type': post.post_type,
                'is_video': post.is_video,
                'hashtags': post.hashtags,
                'media_urls': post.media_urls,
                'url': post_url
            }
            
        except Exception as e:
            logger.error(f"Failed to get post details for {post_url}: {str(e)}")
            return {}
    
    async def get_complete_profile_data(self, username: str, max_posts: int = 10) -> Dict[str, Any]:
        """
        Get complete profile data with detailed posts
        
        Args:
            username: Instagram username
            max_posts: Maximum number of posts to fetch detailed data for
            
        Returns:
            Complete profile data with posts
        """
        logger.info(f"Starting complete data scraping for @{username}")
        
        try:
            # Get profile data and post URLs in parallel
            profile_task = asyncio.to_thread(self.get_profile_data, username)
            posts_urls_task = asyncio.to_thread(self.get_profile_posts_urls, username)
            
            profile_data, post_urls = await asyncio.gather(profile_task, posts_urls_task)
            
            # Limit posts to max_posts
            post_urls = post_urls[:max_posts]
            
            # Get detailed post data in parallel
            logger.info(f"Getting detailed data for {len(post_urls)} posts")
            
            if post_urls:
                post_tasks = [asyncio.to_thread(self.get_post_details, url) for url in post_urls]
                detailed_posts = await asyncio.gather(*post_tasks)
                
                # Filter out empty results
                detailed_posts = [post for post in detailed_posts if post]
            else:
                detailed_posts = []
            
            logger.info(f"Complete scraping finished for @{username}: {len(detailed_posts)} posts with detailed data")
            
            # Build complete data structure
            profile = self.parser.parse_profile_data(self.parser.extract_response_body(
                self._make_api_request(f"https://www.instagram.com/{username}/", 'instagram-profile')
            ))
            
            return {
                'profile': {
                    'username': profile.username,
                    'name': profile.name,
                    'verified': profile.verified,
                    'followersCount': profile.followers_count,
                    'followingCount': profile.following_count,
                    'postsCount': profile.posts_count,
                    'biography': profile.bio,
                    'profilePicUrl': profile.profile_pic_url
                },
                'followers': profile.followers_count,
                'following': profile.following_count,
                'total_posts': profile.posts_count,
                'is_verified': profile.verified,
                'is_business': profile.is_business,
                'biography': profile.bio,
                'external_url': profile.external_url,
                'username': profile.username,
                'posts': detailed_posts
            }
            
        except Exception as e:
            logger.error(f"Complete profile scraping failed for @{username}: {str(e)}")
            raise ValueError(f"Complete scraping failed: {str(e)}")
    
    def calculate_engagement_rate(self, posts_data: List[Dict[str, Any]], followers_count: int) -> float:
        """
        Calculate engagement rate from posts data
        
        Args:
            posts_data: List of post dictionaries with likes and comments
            followers_count: Number of followers
            
        Returns:
            Engagement rate as percentage
        """
        if not posts_data or followers_count == 0:
            return 0.0
        
        total_engagement = 0
        valid_posts = 0
        
        for post in posts_data:
            likes = post.get('likesCount', 0) or 0
            comments = post.get('commentsCount', 0) or 0
            
            if isinstance(likes, int) and isinstance(comments, int):
                total_engagement += (likes + comments)
                valid_posts += 1
        
        if valid_posts == 0:
            return 0.0
        
        avg_engagement = total_engagement / valid_posts
        engagement_rate = (avg_engagement / followers_count) * 100
        
        logger.info(f"Calculated engagement rate: {engagement_rate:.2f}% from {valid_posts} posts")
        
        return round(engagement_rate, 4)
    
    def analyze_posting_frequency(self, posts_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze posting frequency from posts data"""
        if not posts_data:
            return {'post_frequency': 'mai'}
        
        # Simple frequency based on post count
        post_count = len(posts_data)
        if post_count >= 30:
            frequency = 'giornaliera'
        elif post_count >= 15:
            frequency = 'settimanale'
        elif post_count >= 5:
            frequency = 'mensile'
        else:
            frequency = 'sporadica'
        
        return {'post_frequency': frequency}
    
    def analyze_content_performance(self, posts_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze content performance metrics"""
        if not posts_data:
            return {
                'total_posts_analyzed': 0,
                'avg_likes': 0,
                'avg_comments': 0,
                'best_posts': [],
                'video_performance': {'count': 0, 'avg_likes': 0},
                'carousel_performance': {'count': 0, 'avg_likes': 0},
                'image_performance': {'count': 0, 'avg_likes': 0}
            }
        
        total_likes = 0
        total_comments = 0
        video_posts = []
        carousel_posts = []
        image_posts = []
        
        for post in posts_data:
            likes = post.get('likesCount', 0) or 0
            comments = post.get('commentsCount', 0) or 0
            post_type = post.get('type', 'Image')
            
            total_likes += likes
            total_comments += comments
            
            post_info = {
                'likes': likes,
                'comments': comments,
                'type': post_type,
                'url': post.get('url', '')
            }
            
            if post_type == 'Video':
                video_posts.append(post_info)
            elif post_type == 'Sidecar':
                carousel_posts.append(post_info)
            else:
                image_posts.append(post_info)
        
        avg_likes = total_likes / len(posts_data) if posts_data else 0
        avg_comments = total_comments / len(posts_data) if posts_data else 0
        
        # Get best posts
        all_posts = [(p, p.get('likesCount', 0) + p.get('commentsCount', 0)) for p in posts_data]
        best_posts = sorted(all_posts, key=lambda x: x[1], reverse=True)[:3]
        
        return {
            'total_posts_analyzed': len(posts_data),
            'avg_likes': avg_likes,
            'avg_comments': avg_comments,
            'best_posts': [p[0] for p in best_posts],
            'video_performance': {
                'count': len(video_posts),
                'avg_likes': sum(p['likes'] for p in video_posts) / len(video_posts) if video_posts else 0
            },
            'carousel_performance': {
                'count': len(carousel_posts),
                'avg_likes': sum(p['likes'] for p in carousel_posts) / len(carousel_posts) if carousel_posts else 0
            },
            'image_performance': {
                'count': len(image_posts),
                'avg_likes': sum(p['likes'] for p in image_posts) / len(image_posts) if image_posts else 0
            }
        }
    
    def extract_hashtags(self, posts_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract and analyze hashtags from posts"""
        if not posts_data:
            return {
                'avg_hashtags_per_post': 0,
                'unique_hashtags': 0,
                'top_hashtags': []
            }
        
        hashtag_counts = {}
        total_hashtags = 0
        
        for post in posts_data:
            hashtags = post.get('hashtags', [])
            total_hashtags += len(hashtags)
            
            for tag in hashtags:
                tag_lower = tag.lower()
                hashtag_counts[tag_lower] = hashtag_counts.get(tag_lower, 0) + 1
        
        avg_hashtags = total_hashtags / len(posts_data) if posts_data else 0
        top_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'avg_hashtags_per_post': avg_hashtags,
            'unique_hashtags': len(hashtag_counts),
            'top_hashtags': top_hashtags
        }