"""
Crawlbase Instagram Data Parser

Clean, maintainable parser for Instagram data from Crawlbase API.
Handles the specific format and structure returned by Crawlbase scrapers.
"""

import re
import json
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from app.utils.logger import setup_logger
from app.utils.retry import retry_external_calls, with_retry_logging

logger = setup_logger(__name__)


@dataclass
class InstagramProfile:
    """Parsed Instagram profile data"""
    username: str
    name: str
    verified: bool
    followers_count: int
    following_count: int
    posts_count: int
    bio: str
    profile_pic_url: str
    is_business: bool = False
    external_url: str = ""


@dataclass
class InstagramPost:
    """Parsed Instagram post data"""
    shortcode: str
    likes_count: int
    comments_count: int
    caption: str
    timestamp: str
    post_type: str
    is_video: bool
    hashtags: List[str]
    media_urls: List[str]


class CrawlbaseParser:
    """Parser for Crawlbase Instagram API responses"""
    
    def __init__(self):
        """Initialize the parser"""
        pass
    
    @retry_external_calls
    @with_retry_logging
    def extract_response_body(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract the actual Instagram data from Crawlbase response wrapper
        
        Args:
            response: Raw response from Crawlbase API
            
        Returns:
            Dictionary containing Instagram data
            
        Raises:
            ValueError: If response format is invalid
        """
        if not isinstance(response, dict):
            raise ValueError(f"Expected dict response, got {type(response)}")
        
        if 'body' not in response:
            logger.error(
                f"No 'body' field in response",
                extra={"response_keys": list(response.keys())}
            )
            raise ValueError("Invalid Crawlbase response - missing body field")
        
        body = response['body']
        
        # Handle different body formats
        if isinstance(body, dict):
            return body
        elif isinstance(body, (str, bytes)):
            if isinstance(body, bytes):
                body = body.decode('utf-8')
            
            try:
                return json.loads(body)
            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse body JSON",
                    extra={"error": str(e), "body_preview": body[:200] if body else ""},
                    exc_info=True
                )
                raise ValueError(f"Invalid JSON in response body: {str(e)}")
        else:
            raise ValueError(f"Unexpected body type: {type(body)}")
    
    def parse_count_string(self, count_str: Union[str, int, Dict[str, Any]]) -> int:
        """
        Parse Instagram count strings with various formats
        
        Handles:
        - "34.2M followers" -> 34200000
        - "1,263 posts" -> 1263
        - {"value": "123K", "text": "123K"} -> 123000
        - Direct integers
        
        Args:
            count_str: Count value in various formats
            
        Returns:
            Parsed integer count
        """
        if isinstance(count_str, int):
            return count_str
        
        if isinstance(count_str, dict):
            # Handle Crawlbase format: {"value": "123K", "text": "123K"}
            value = count_str.get('value', '0')
            if isinstance(value, int):
                return value
            count_str = str(value)
        
        if not isinstance(count_str, str):
            return 0
        
        # Clean the string
        clean_str = count_str.lower().strip()
        
        # Remove common suffixes
        clean_str = re.sub(r'\s*(followers?|following|posts?)\s*$', '', clean_str)
        
        try:
            # Handle M, K suffixes (including international variants)
            if any(indicator in clean_str for indicator in ['m', 'млн', 'million']):
                # "34.2m", "34,2 млн подписчиков" -> 34200000
                # Extract number part before million indicator
                num_match = re.search(r'([\d,.\s]+)', clean_str)
                if num_match:
                    num_part = num_match.group(1).replace(',', '.').replace(' ', '').strip()
                    return int(float(num_part) * 1_000_000)
            elif any(indicator in clean_str for indicator in ['k', 'тыс', 'thousand']):
                # "123.4k", "123 тыс" -> 123400
                num_match = re.search(r'([\d,.\s]+)', clean_str)
                if num_match:
                    num_part = num_match.group(1).replace(',', '.').replace(' ', '').strip()
                    return int(float(num_part) * 1_000)
            else:
                # Handle regular numbers with commas: "1,263" -> 1263
                clean_num = re.sub(r'[^\d]', '', clean_str)
                return int(clean_num) if clean_num else 0
                
        except (ValueError, TypeError):
            # Fallback: extract first sequence of digits
            numbers = re.findall(r'[\d,]+', str(count_str))
            if numbers:
                try:
                    return int(numbers[0].replace(',', ''))
                except ValueError:
                    pass
            
            logger.warning(f"Could not parse count string: {count_str}")
            return 0
    
    def parse_profile_data(self, raw_data: Dict[str, Any]) -> InstagramProfile:
        """
        Parse Instagram profile data from Crawlbase response
        
        Args:
            raw_data: Raw Instagram data from Crawlbase body
            
        Returns:
            Parsed InstagramProfile object
        """
        # Extract basic info
        username = raw_data.get('username', '')
        name = raw_data.get('name', '')
        verified = raw_data.get('verified', False)
        profile_pic_url = raw_data.get('picture', '')
        
        # Parse bio
        bio_data = raw_data.get('bio', '')
        if isinstance(bio_data, dict):
            bio = bio_data.get('text', '')
        else:
            bio = str(bio_data) if bio_data else ''
        
        # Parse counts - IMPORTANT: Crawlbase has INVERTED field names!
        # Based on analysis: followersCount has small numbers, followingCount has large numbers
        followers_raw = raw_data.get('followersCount', {})  # Actually contains following count
        following_raw = raw_data.get('followingCount', {})  # Actually contains followers count  
        posts_raw = raw_data.get('postsCount', {})
        
        # Parse the raw values
        small_number = self.parse_count_string(followers_raw)    # followersCount = actual following
        large_number = self.parse_count_string(following_raw)    # followingCount = actual followers
        posts_count = self.parse_count_string(posts_raw)
        
        # Crawlbase field mapping (based on real data analysis):
        # - followersCount field contains the FOLLOWING count (smaller number)
        # - followingCount field contains the FOLLOWERS count (larger number)
        followers_count = large_number  # Use followingCount value as followers
        following_count = small_number  # Use followersCount value as following
        
        # Log only for successful parsing with real data
        if followers_count > 0 or posts_count > 0:
            logger.info(f"Parsed profile @{username}: {followers_count:,} followers, {posts_count} posts")
        
        return InstagramProfile(
            username=username,
            name=name,
            verified=verified,
            followers_count=followers_count,
            following_count=following_count,
            posts_count=posts_count,
            bio=bio,
            profile_pic_url=profile_pic_url,
            is_business=False,  # Not reliably available from Crawlbase
            external_url=""     # Not reliably available from Crawlbase
        )
    
    def extract_hashtags_from_text(self, text: str) -> List[str]:
        """Extract hashtags from text"""
        if not text:
            return []
        
        hashtags = re.findall(r'#(\w+)', text)
        return [tag.lower() for tag in hashtags]
    
    def parse_post_data(self, raw_data: Dict[str, Any]) -> InstagramPost:
        """
        Parse Instagram post data from Crawlbase instagram-post scraper
        
        Based on real API analysis:
        - likesCount: direct integer (e.g., 343531)
        - repliesCount: comments count (e.g., 0) 
        - caption: {text: "...", tags: [...]}
        - dateTime: ISO timestamp
        - media: {images: [...], videos: [...]}
        
        Args:
            raw_data: Raw post data from Crawlbase body
            
        Returns:
            Parsed InstagramPost object
        """
        # Extract engagement metrics (confirmed format)
        likes_count = raw_data.get('likesCount', 0)
        comments_count = raw_data.get('repliesCount', 0)  # Crawlbase uses 'repliesCount'
        timestamp = raw_data.get('dateTime', '')
        
        # Extract caption and hashtags
        caption_data = raw_data.get('caption', {})
        caption = ''
        hashtags = []
        
        if isinstance(caption_data, dict):
            caption = caption_data.get('text', '')
            
            # Extract hashtags from structured tags
            tags = caption_data.get('tags', [])
            for tag in tags:
                if isinstance(tag, dict):
                    if 'hashtag' in tag:
                        hashtag = tag['hashtag'].lstrip('#')
                        hashtags.append(hashtag.lower())
        else:
            caption = str(caption_data) if caption_data else ''
        
        # Fallback: extract hashtags from caption text if tags are empty
        if not hashtags and caption:
            hashtags = self.extract_hashtags_from_text(caption)
        
        # Determine post type and media
        media_data = raw_data.get('media', {})
        media_urls = []
        is_video = False
        post_type = 'Image'
        
        if isinstance(media_data, dict):
            videos = media_data.get('videos', [])
            images = media_data.get('images', [])
            
            if videos and len(videos) > 0:
                is_video = True
                post_type = 'Video'
                media_urls.extend(videos)
            
            if images and len(images) > 0:
                media_urls.extend(images)
                if len(images) > 1 and post_type == 'Image':
                    post_type = 'Sidecar'
        
        # Extract shortcode
        shortcode = ''
        if 'url' in raw_data:
            url = raw_data['url']
            if '/p/' in url:
                shortcode = url.split('/p/')[-1].split('/')[0]
        
        if not shortcode:
            clean_timestamp = timestamp.replace(':', '').replace('-', '').replace('T', '').replace('Z', '')
            shortcode = f"post_{clean_timestamp}"
        
        return InstagramPost(
            shortcode=shortcode,
            likes_count=int(likes_count) if isinstance(likes_count, (int, str)) and str(likes_count).isdigit() else 0,
            comments_count=int(comments_count) if isinstance(comments_count, (int, str)) and str(comments_count).isdigit() else 0,
            caption=caption,
            timestamp=timestamp,
            post_type=post_type,
            is_video=is_video,
            hashtags=hashtags,
            media_urls=media_urls
        )
    
    def parse_profile_posts(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse posts from profile data (lighter data, for URLs mainly)
        
        Args:
            raw_data: Raw profile data from Crawlbase body
            
        Returns:
            List of post dictionaries with basic info
        """
        posts_data = raw_data.get('posts', [])
        if not posts_data:
            return []
        
        parsed_posts = []
        for post in posts_data:
            if not isinstance(post, dict):
                continue
            
            # Extract post URL for detailed scraping
            post_link = post.get('link', '')
            if not post_link:
                continue
            
            # Extract shortcode from URL
            shortcode = ''
            if '/p/' in post_link:
                shortcode = post_link.split('/p/')[-1].rstrip('/')
            
            parsed_posts.append({
                'link': post_link,
                'shortcode': shortcode,
                'preview_data': post  # Keep original data for fallback
            })
        
        return parsed_posts