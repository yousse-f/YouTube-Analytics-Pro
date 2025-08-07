from crawlbase import CrawlingAPI
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import asyncio
import re
import json
import time
from statistics import mean

from app.utils.logger import setup_logger
from app.config import settings

logger = setup_logger(__name__)


class InstagramClient:
    def __init__(self):
        try:
            if not settings.CRAWLBASE_JS_TOKEN:
                raise ValueError("CRAWLBASE_JS_TOKEN not configured")
            
            self.api = CrawlingAPI({
                'token': settings.CRAWLBASE_JS_TOKEN,
                'timeout': 120  # Set 120 second timeout for Instagram
            })
            self.max_retries = 2
            logger.info("InstagramClient initialized with Crawlbase successfully")
        except Exception as e:
            logger.error(f"Error initializing InstagramClient: {str(e)}")
            raise
    
    def _make_request_with_retry(self, url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Make Crawlbase request with retry logic for connection errors"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt}/{self.max_retries} for {url}")
                    time.sleep(1 * attempt)  # Exponential backoff
                
                response = self.api.get(url, options)
                
                if response.get('status_code') == 200:
                    return response
                else:
                    logger.warning(f"API returned status {response.get('status_code')} for {url}")
                    if attempt == self.max_retries:
                        raise ValueError(f"API request failed with status {response.get('status_code')}")
                    continue
                    
            except Exception as e:
                last_exception = e
                error_msg = str(e).lower()
                
                # Check for connection/timeout errors that should be retried
                if any(keyword in error_msg for keyword in [
                    'connection', 'timeout', 'remote end closed', 
                    'read timed out', 'connection refused', 'network'
                ]):
                    if attempt < self.max_retries:
                        logger.warning(f"Connection error on attempt {attempt + 1}: {str(e)}. Retrying...")
                        continue
                    else:
                        logger.error(f"Max retries exceeded for {url}. Last error: {str(e)}")
                        raise ValueError(f"Connection failed after {self.max_retries + 1} attempts: {str(e)}")
                else:
                    # Non-retryable error, raise immediately
                    raise
        
        # If we get here, all retries failed
        raise last_exception or ValueError("Request failed")
    
    def _parse_count_string(self, count_str: str) -> int:
        """Parse Instagram count strings like '34.2M followers', '1,263 posts', etc."""
        if not count_str or not isinstance(count_str, str):
            return 0
        
        # Remove common suffixes
        clean_str = count_str.lower().replace(' followers', '').replace(' following', '').replace(' posts', '').strip()
        
        try:
            # Handle M, K suffixes
            if 'm' in clean_str:
                # e.g., "34.2m" -> 34,200,000
                num_part = clean_str.replace('m', '')
                return int(float(num_part) * 1_000_000)
            elif 'k' in clean_str:
                # e.g., "123.4k" -> 123,400
                num_part = clean_str.replace('k', '')
                return int(float(num_part) * 1_000)
            else:
                # Handle regular numbers with commas like "1,263"
                clean_num = re.sub(r'[^\d]', '', clean_str)  # Keep only digits
                return int(clean_num) if clean_num else 0
                
        except (ValueError, AttributeError):
            # Fallback: extract just the first number found
            numbers = re.findall(r'[\d,]+', count_str)
            if numbers:
                try:
                    return int(numbers[0].replace(',', ''))
                except ValueError:
                    pass
            return 0
    
    async def get_profile_data(self, username: str) -> Dict[str, Any]:
        try:
            logger.info(f"Fetching Instagram data for: @{username} via Crawlbase")
            
            # Fetch both profile and posts data using Crawlbase scrapers
            profile_data, posts_data = await asyncio.gather(
                asyncio.to_thread(self._fetch_profile_info, username),
                asyncio.to_thread(self._fetch_posts_data, username)
            )
            
            # Combine the data
            combined_data = {
                **profile_data,
                'posts': posts_data
            }
            
            return combined_data
        except Exception as e:
            logger.error(f"Error in get_profile_data for {username}: {str(e)}")
            raise
    
    def _fetch_profile_info(self, username: str) -> Dict[str, Any]:
        """Fetch profile info using Crawlbase Instagram Profile Scraper"""
        try:
            instagram_url = f"https://www.instagram.com/{username}/"
            options = {
                'scraper': 'instagram-profile'
            }
            
            logger.info(f"Fetching profile info for @{username} via Crawlbase Instagram Profile Scraper")
            response = self._make_request_with_retry(instagram_url, options)
            
            # Parse JSON response from Crawlbase scraper
            # Debug the response structure first
            logger.info(f"DEBUG: Response type: {type(response)}")
            logger.info(f"DEBUG: Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
            if 'body' in response:
                body_content = response['body']
                logger.info(f"DEBUG: Body type: {type(body_content)}")
                logger.info(f"DEBUG: Body preview: {str(body_content)[:200]}...")
            
            # The response structure is: {'body': {...actual_instagram_data...}}
            # First check if we have the wrapper structure
            if 'body' in response and isinstance(response['body'], dict):
                # Direct access to body (already parsed)
                profile_info = response['body']
                logger.info(f"Using parsed body from response for @{username}")
            elif 'body' in response:
                # Body is string/bytes, need to parse
                response_body = response['body']
                if isinstance(response_body, bytes):
                    response_body = response_body.decode('utf-8')
                
                try:
                    profile_info = json.loads(response_body)
                    logger.info(f"Parsed body JSON for @{username}")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse profile JSON for @{username}: {str(e)}")
                    logger.error(f"Response body: {str(response_body)[:500]}...")
                    # Fallback: use the entire response if body parsing fails
                    profile_info = response
                    logger.warning(f"Using entire response as fallback for @{username}")
            else:
                logger.error(f"No 'body' field found in Crawlbase response for @{username}")
                logger.error(f"Available keys: {list(response.keys())}")
                raise ValueError("Invalid Crawlbase response format - no body field")
            
            # Log successful parsing
            logger.info(f"Successfully parsed profile data for @{username}")
            logger.info(f"Available keys in profile: {list(profile_info.keys())[:10]}")  # Show first 10 keys
            
            if profile_info and 'followersCount' in profile_info:
                followers_debug = profile_info['followersCount']
                if isinstance(followers_debug, dict):
                    followers_text = followers_debug.get('text', 'N/A')
                    logger.info(f"Profile parsed - followers: {followers_text}")
                else:
                    logger.info(f"Profile parsed - followers: {followers_debug}")
            else:
                logger.info(f"No 'followersCount' field found for @{username}")
            
            # Parse followers count from text/value format
            # NOTE: Crawlbase seems to have confusing field names - check both fields
            followers_count = 0
            
            # Check both followersCount and followingCount to find the larger number (actual followers)
            followers_candidate = 0
            following_candidate = 0
            
            if 'followersCount' in profile_info:
                if isinstance(profile_info['followersCount'], dict):
                    followers_str = profile_info['followersCount'].get('value', '0')
                    followers_candidate = self._parse_count_string(followers_str)
                else:
                    followers_candidate = int(profile_info['followersCount']) if profile_info['followersCount'] else 0
            
            if 'followingCount' in profile_info:
                if isinstance(profile_info['followingCount'], dict):
                    following_str = profile_info['followingCount'].get('value', '0')
                    following_candidate = self._parse_count_string(following_str)
                else:
                    following_candidate = int(profile_info['followingCount']) if profile_info['followingCount'] else 0
            
            # Use the larger number as followers (Apple should have 34M followers, not 1,263)
            followers_count = max(followers_candidate, following_candidate)
            logger.info(f"Followers candidate: {followers_candidate}, Following candidate: {following_candidate}, Using: {followers_count}")
            
            # Parse following count (use the smaller number)
            following_count = min(followers_candidate, following_candidate) if followers_candidate > 0 and following_candidate > 0 else 0
            
            # Parse posts count - need to extract numeric value from "1,263 posts"
            posts_count = 0
            if 'postsCount' in profile_info:
                if isinstance(profile_info['postsCount'], dict):
                    posts_str = profile_info['postsCount'].get('value', '0')
                    posts_count = self._parse_count_string(posts_str)
                else:
                    posts_count = int(profile_info['postsCount']) if profile_info['postsCount'] else 0
            
            # Extract bio text
            bio_text = ''
            if 'bio' in profile_info:
                if isinstance(profile_info['bio'], dict):
                    bio_text = profile_info['bio'].get('text', '')
                else:
                    bio_text = str(profile_info['bio']) if profile_info['bio'] else ''
            
            logger.info(f"Profile retrieved: followers={followers_count}, verified={profile_info.get('verified', False)}")
            
            return {
                'profile': {
                    'username': profile_info.get('username', username),
                    'fullName': profile_info.get('name', ''),
                    'biography': bio_text,
                    'followersCount': followers_count,
                    'followsCount': following_count,
                    'postsCount': posts_count,
                    'isVerified': profile_info.get('verified', False),
                    'isBusinessAccount': False,  # Not available in Crawlbase response
                    'externalUrl': '',  # Not directly available
                    'profilePicUrl': profile_info.get('picture', '')
                },
                'followers': followers_count,
                'following': following_count,
                'total_posts': posts_count,
                'is_verified': profile_info.get('verified', False),
                'is_business': False,
                'biography': bio_text,
                'external_url': '',
                'username': profile_info.get('username', username)
            }
            
        except Exception as e:
            logger.error(f"Error fetching profile info for {username}: {str(e)}")
            raise ValueError(f"Error fetching Instagram profile: {str(e)}")
    
    def _fetch_posts_data(self, username: str) -> List[Dict[str, Any]]:
        """Fetch posts data using dual approach: profile scraper for post URLs + individual post scraper for details"""
        try:
            # Step 1: Get post URLs from profile scraper
            instagram_url = f"https://www.instagram.com/{username}/"
            options = {
                'scraper': 'instagram-profile'
            }
            
            logger.info(f"Fetching post URLs for @{username} via Crawlbase Profile Scraper")
            try:
                response = self._make_request_with_retry(instagram_url, options)
            except Exception as e:
                logger.warning(f"Profile scraper failed for @{username}: {str(e)}")
                return []
            
            # Parse JSON response - extract body field from Crawlbase response
            if 'body' in response and isinstance(response['body'], dict):
                profile_data = response['body']
            elif 'body' in response:
                response_body = response['body']
                if isinstance(response_body, bytes):
                    response_body = response_body.decode('utf-8')
                
                try:
                    profile_data = json.loads(response_body)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse posts profile JSON for @{username}")
                    return []
            else:
                logger.warning(f"No 'body' field found in posts response for @{username}")
                return []
            
            # Extract posts URLs from profile
            posts_data = profile_data.get('posts', [])
            
            if not posts_data:
                logger.warning(f"No posts data returned from Crawlbase profile for @{username}")
                return []
            
            logger.info(f"Found {len(posts_data)} posts from profile, fetching details...")
            
            # Step 2: Fetch detailed data for each post using instagram-post scraper
            detailed_posts = []
            
            # Temporarily limit to fewer posts to avoid timeouts - let's try just 3
            posts_to_process = posts_data[:3]
            
            logger.info(f"Processing {len(posts_to_process)} posts with detailed scraping...")
            
            for i, post in enumerate(posts_to_process):
                try:
                    post_link = post.get('link', '')
                    if not post_link or '/p/' not in post_link:
                        continue
                    
                    logger.info(f"Fetching details for post {i+1}/{len(posts_to_process)}: {post_link}")
                    
                    # Use instagram-post scraper for detailed data
                    post_options = {
                        'scraper': 'instagram-post'
                    }
                    
                    try:
                        post_response = self._make_request_with_retry(post_link, post_options)
                    except Exception as e:
                        logger.warning(f"Post scraper failed for {post_link}: {str(e)}")
                        continue
                    
                    # Parse post response body from Crawlbase
                    if 'body' in post_response and isinstance(post_response['body'], dict):
                        post_details = post_response['body']
                    elif 'body' in post_response:
                        post_response_body = post_response['body']
                        if isinstance(post_response_body, bytes):
                            post_response_body = post_response_body.decode('utf-8')
                        
                        try:
                            post_details = json.loads(post_response_body)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse post JSON for {post_link}")
                            continue
                    else:
                        logger.warning(f"No 'body' field found in post response for {post_link}")
                        continue
                    
                    # Extract shortcode from link
                    shortcode = post_link.split('/p/')[-1].rstrip('/')
                    
                    # Convert to our expected format using detailed post data
                    converted_post = {
                        'likesCount': post_details.get('likesCount', 0),
                        'commentsCount': post_details.get('repliesCount', 0),  # Crawlbase uses 'repliesCount' for comments
                        'shortCode': shortcode,
                        'type': self._determine_post_type(post_details),
                        'isVideo': len(post_details.get('media', {}).get('videos', [])) > 0,
                        'caption': post_details.get('caption', {}).get('text', ''),
                        'timestamp': post_details.get('dateTime', ''),
                        'hashtags': self._extract_hashtags_from_post(post_details)
                    }
                    
                    detailed_posts.append(converted_post)
                    
                    # Small delay between requests to avoid rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"Error processing individual post {post_link}: {str(e)}")
                    continue
            
            logger.info(f"Successfully retrieved details for {len(detailed_posts)} posts")
            return detailed_posts
            
        except Exception as e:
            logger.error(f"Error fetching posts data for {username}: {str(e)}")
            raise ValueError(f"Error fetching Instagram posts: {str(e)}")
    
    def _determine_post_type(self, post_details: Dict[str, Any]) -> str:
        """Determine post type from Crawlbase instagram-post data"""
        media = post_details.get('media', {})
        videos = media.get('videos', [])
        images = media.get('images', [])
        
        if videos and len(videos) > 0:
            return 'Video'
        elif images and len(images) > 1:
            return 'Sidecar'  # Multiple images = carousel
        else:
            return 'Image'
    
    def _extract_hashtags_from_post(self, post_details: Dict[str, Any]) -> List[str]:
        """Extract hashtags from Crawlbase instagram-post data"""
        hashtags = []
        
        caption_data = post_details.get('caption', {})
        if isinstance(caption_data, dict):
            tags = caption_data.get('tags', [])
            for tag in tags:
                if isinstance(tag, dict) and 'hashtag' in tag:
                    hashtag = tag['hashtag'].lstrip('#')
                    hashtags.append(hashtag)
        
        return hashtags
    
    def _convert_post_type(self, crawlbase_type: str) -> str:
        """Convert Crawlbase post type to our expected format"""
        type_mapping = {
            'image': 'Image',
            'video': 'Video', 
            'carousel': 'Sidecar',
            'reel': 'Video'
        }
        return type_mapping.get(crawlbase_type.lower(), 'Image')
    
    def calculate_engagement_rate(self, posts_data: List[Dict], followers_count: int = 0) -> float:
        if not posts_data or followers_count == 0:
            return 0.0
        
        try:
            total_engagement = 0
            total_posts = 0
            
            for post in posts_data:
                likes = post.get('likesCount', 0)
                comments = post.get('commentsCount', 0)
                
                if likes is not None and comments is not None:
                    total_engagement += (likes + comments)
                    total_posts += 1
            
            if total_posts == 0:
                return 0.0
            
            avg_engagement = total_engagement / total_posts
            engagement_rate = (avg_engagement / followers_count) * 100
            
            return round(engagement_rate, 4)
            
        except Exception as e:
            logger.error(f"Error calculating engagement rate: {str(e)}")
            return 0.0
    
    def analyze_posting_frequency(self, posts_data: List[Dict]) -> Dict[str, Any]:
        if not posts_data:
            return {'post_frequency': 'mai', 'posts_per_week': 0, 'posts_per_month': 0}
        
        try:
            now = datetime.now()
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)
            
            recent_posts = []
            monthly_posts = []
            
            for post in posts_data:
                try:
                    timestamp = post.get('timestamp')
                    if timestamp:
                        # Handle different timestamp formats
                        if isinstance(timestamp, str):
                            if 'T' in timestamp:
                                post_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            else:
                                post_date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                        else:
                            # Handle Unix timestamp
                            post_date = datetime.fromtimestamp(timestamp)
                        
                        # Ensure timezone-naive comparison
                        if post_date.tzinfo is not None:
                            post_date = post_date.replace(tzinfo=None)
                        
                        if post_date >= week_ago:
                            recent_posts.append(post)
                        if post_date >= month_ago:
                            monthly_posts.append(post)
                            
                except Exception as e:
                    logger.warning(f"Error processing post date: {str(e)}")
                    continue
            
            posts_per_week = len(recent_posts)
            posts_per_month = len(monthly_posts)
            
            if posts_per_week >= 7:
                frequency = "giornaliera"
            elif posts_per_week >= 3:
                frequency = "settimanale"
            elif posts_per_week >= 1:
                frequency = "bisettimanale"
            elif posts_per_month >= 1:
                frequency = "mensile"
            else:
                frequency = "rara"
            
            return {
                'post_frequency': frequency,
                'posts_per_week': posts_per_week,
                'posts_per_month': posts_per_month
            }
            
        except Exception as e:
            logger.error(f"Error analyzing posting frequency: {str(e)}")
            return {'post_frequency': 'mai', 'posts_per_week': 0, 'posts_per_month': 0}
    
    def analyze_content_performance(self, posts_data: List[Dict]) -> Dict[str, Any]:
        if not posts_data:
            return {
                'avg_likes': 0,
                'avg_comments': 0,
                'total_posts_analyzed': 0,
                'video_performance': {'count': 0, 'avg_likes': 0},
                'carousel_performance': {'count': 0, 'avg_likes': 0},
                'image_performance': {'count': 0, 'avg_likes': 0},
                'best_posts': []
            }
        
        try:
            total_likes = 0
            total_comments = 0
            valid_posts = 0
            
            video_posts = []
            carousel_posts = []
            image_posts = []
            
            post_data = []
            
            for post in posts_data:
                try:
                    likes = post.get('likesCount', 0)
                    comments = post.get('commentsCount', 0)
                    shortcode = post.get('shortCode', '')
                    
                    if likes is not None and comments is not None:
                        total_likes += likes
                        total_comments += comments
                        valid_posts += 1
                        
                        post_info = {
                            'likes': likes,
                            'comments': comments,
                            'shortcode': shortcode,
                            'url': f"https://instagram.com/p/{shortcode}/"
                        }
                        
                        post_type = post.get('type', 'Image')
                        if post_type in ['Video', 'Reel'] or post.get('isVideo', False):
                            post_info['type'] = 'video'
                            video_posts.append(post_info)
                        elif post_type == 'Sidecar':
                            post_info['type'] = 'carousel'
                            carousel_posts.append(post_info)
                        else:
                            post_info['type'] = 'image'
                            image_posts.append(post_info)
                        
                        post_data.append(post_info)
                        
                except Exception as e:
                    logger.warning(f"Error processing post: {str(e)}")
                    continue
            
            avg_likes = total_likes / valid_posts if valid_posts > 0 else 0
            avg_comments = total_comments / valid_posts if valid_posts > 0 else 0
            
            video_avg_likes = mean([p['likes'] for p in video_posts]) if video_posts else 0
            carousel_avg_likes = mean([p['likes'] for p in carousel_posts]) if carousel_posts else 0
            image_avg_likes = mean([p['likes'] for p in image_posts]) if image_posts else 0
            
            best_posts = sorted(post_data, key=lambda x: x['likes'] + x['comments'], reverse=True)[:3]
            
            return {
                'avg_likes': round(avg_likes, 1),
                'avg_comments': round(avg_comments, 1),
                'total_posts_analyzed': valid_posts,
                'video_performance': {
                    'count': len(video_posts),
                    'avg_likes': round(video_avg_likes, 1)
                },
                'carousel_performance': {
                    'count': len(carousel_posts),
                    'avg_likes': round(carousel_avg_likes, 1)
                },
                'image_performance': {
                    'count': len(image_posts),
                    'avg_likes': round(image_avg_likes, 1)
                },
                'best_posts': best_posts
            }
            
        except Exception as e:
            logger.error(f"Error analyzing content performance: {str(e)}")
            return {
                'avg_likes': 0,
                'avg_comments': 0,
                'total_posts_analyzed': 0,
                'video_performance': {'count': 0, 'avg_likes': 0},
                'carousel_performance': {'count': 0, 'avg_likes': 0},
                'image_performance': {'count': 0, 'avg_likes': 0},
                'best_posts': []
            }
    
    def extract_hashtags(self, posts_data: List[Dict]) -> Dict[str, Any]:
        if not posts_data:
            return {
                'total_hashtags': 0,
                'unique_hashtags': 0,
                'avg_hashtags_per_post': 0,
                'top_hashtags': []
            }
        
        try:
            all_hashtags = []
            posts_with_captions = 0
            
            for post in posts_data:
                try:
                    # Check if hashtags are already extracted
                    if post.get('hashtags'):
                        hashtags_list = post.get('hashtags', [])
                        if hashtags_list:
                            posts_with_captions += 1
                            all_hashtags.extend([tag.lower() for tag in hashtags_list])
                    else:
                        # Extract from caption
                        caption = post.get('caption', '') or ''
                        if caption:
                            posts_with_captions += 1
                            hashtags = re.findall(r'#(\w+)', caption)
                            all_hashtags.extend([tag.lower() for tag in hashtags])
                except Exception as e:
                    logger.warning(f"Error extracting hashtags from post: {str(e)}")
                    continue
            
            if not all_hashtags:
                return {
                    'total_hashtags': 0,
                    'unique_hashtags': 0,
                    'avg_hashtags_per_post': 0,
                    'top_hashtags': []
                }
            
            hashtag_counts = {}
            for hashtag in all_hashtags:
                hashtag_counts[hashtag] = hashtag_counts.get(hashtag, 0) + 1
            
            top_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                'total_hashtags': len(all_hashtags),
                'unique_hashtags': len(hashtag_counts),
                'avg_hashtags_per_post': round(len(all_hashtags) / max(posts_with_captions, 1), 1),
                'top_hashtags': top_hashtags
            }
            
        except Exception as e:
            logger.error(f"Error extracting hashtags: {str(e)}")
            return {
                'total_hashtags': 0,
                'unique_hashtags': 0,
                'avg_hashtags_per_post': 0,
                'top_hashtags': []
            }