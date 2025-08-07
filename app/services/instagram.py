# app/services/instagram.py
from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncio

from app.models.instagram import (
    InstagramScrapingResult,
    ProfileAndPresence,
    FrequencyAndActivity,
    KPIAndPerformance,
    ContentAndFormat,
    InstagramToneOfVoice,
    TrendsAndHashtags,
    InstagramFunnelAndObjectives,
)
from app.utils import InstagramClientV2, TextAnalyzer, setup_logger

logger = setup_logger(__name__)


class InstagramScraper:
    def __init__(self):
        self.client = InstagramClientV2()
        self.text_analyzer = TextAnalyzer()

    async def scrape(self, username: str) -> InstagramScrapingResult:
        try:
            logger.info(f"Starting real Instagram scraping for: @{username}")

            # Get complete profile data with posts using new client
            profile_data = await self.client.get_complete_profile_data(
                username, max_posts=8
            )

            results = await asyncio.gather(
                self._analyze_profile_presence(profile_data),
                self._analyze_frequency_activity(profile_data),
                self._analyze_kpi_performance(profile_data),
                self._analyze_content_format(profile_data),
                self._analyze_tone_of_voice(profile_data),
                self._analyze_trends_hashtags(profile_data),
                self._analyze_funnel_objectives(profile_data),
                return_exceptions=True,
            )

            # Handle exceptions and create fallback objects
            profile_presence = (
                results[0]
                if not isinstance(results[0], Exception)
                else ProfileAndPresence(current_followers=0, total_posts=0)
            )

            frequency_activity = (
                results[1]
                if not isinstance(results[1], Exception)
                else FrequencyAndActivity(
                    posting_frequency={
                        "post": "mai",
                        "reel": "mai",
                        "stories": "non_disponibile",
                        "live": "non_disponibile",
                    },
                    content_statistics={
                        "note": "Dati non disponibili a causa di errore"
                    },
                )
            )

            kpi_performance = (
                results[2]
                if not isinstance(results[2], Exception)
                else KPIAndPerformance(
                    engagement_rate=0.0,
                    avg_likes_per_post=0.0,
                    avg_comments_per_post=0.0,
                    avg_interactions_per_post=0.0,
                )
            )

            content_format = (
                results[3]
                if not isinstance(results[3], Exception)
                else ContentAndFormat(
                    content_types={"note": "Dati non disponibili a causa di errore"},
                    creative_analysis="minimal",
                    best_content=[],
                )
            )

            tone_of_voice = (
                results[4]
                if not isinstance(results[4], Exception)
                else InstagramToneOfVoice(tone="professionale")
            )

            trends_hashtags = (
                results[5]
                if not isinstance(results[5], Exception)
                else TrendsAndHashtags(
                    active_trends=False,
                    effective_formats=False,
                    hashtag_analysis="Dati non disponibili a causa di errore",
                )
            )

            funnel_objectives = (
                results[6]
                if not isinstance(results[6], Exception)
                else InstagramFunnelAndObjectives(
                    profile_objective="awareness", brand_ambassadors=False
                )
            )

            result = InstagramScrapingResult(
                username=username,
                scraping_date=datetime.now().isoformat(),
                profile_presence=profile_presence,
                frequency_activity=frequency_activity,
                kpi_performance=kpi_performance,
                content_format=content_format,
                tone_of_voice=tone_of_voice,
                trends_hashtags=trends_hashtags,
                funnel_objectives=funnel_objectives,
            )

            logger.info(f"Instagram scraping completed for: @{username}")
            return result

        except Exception as e:
            logger.error(f"Error scraping Instagram @{username}: {str(e)}")
            return InstagramScrapingResult(
                username=username,
                scraping_date=datetime.now().isoformat(),
                error_message=str(e),
            )

    async def _analyze_profile_presence(
        self, profile_data: Dict[str, Any]
    ) -> ProfileAndPresence:
        try:
            # Use clean data structure from V2 client
            followers = profile_data.get("followers", 0)
            total_posts = profile_data.get("total_posts", 0)

            return ProfileAndPresence(
                current_followers=followers,
                total_posts=total_posts,
                follower_growth=None,
                quality_estimate=None,
            )
        except Exception as e:
            logger.error(f"Error analyzing profile presence: {str(e)}")
            logger.error(f"Profile data structure: {profile_data}")
            raise

    async def _analyze_frequency_activity(
        self, profile_data: Dict[str, Any]
    ) -> FrequencyAndActivity:
        try:
            posts_data = profile_data["posts"]

            frequency_data = self.client.analyze_posting_frequency(posts_data)
            content_performance = self.client.analyze_content_performance(posts_data)

            posting_frequency = {
                "post": frequency_data.get("post_frequency", "mai"),
                "stories": "non_disponibile",
                "reel": frequency_data.get("post_frequency", "mai"),
                "live": "non_disponibile",
            }

            content_statistics = {
                "post": {
                    "total": content_performance.get("total_posts_analyzed", 0),
                    "avg_likes": content_performance.get("avg_likes", 0),
                    "avg_comments": content_performance.get("avg_comments", 0),
                },
                "reel": {
                    "total": content_performance.get("video_performance", {}).get(
                        "count", 0
                    ),
                    "avg_likes": content_performance.get("video_performance", {}).get(
                        "avg_likes", 0
                    ),
                    "avg_comments": content_performance.get("avg_comments", 0),
                },
                "carousel": {
                    "total": content_performance.get("carousel_performance", {}).get(
                        "count", 0
                    ),
                    "avg_likes": content_performance.get(
                        "carousel_performance", {}
                    ).get("avg_likes", 0),
                    "avg_comments": content_performance.get("avg_comments", 0),
                },
                "stories": {
                    "note": "Dati stories non disponibili tramite API pubblica"
                },
            }

            return FrequencyAndActivity(
                posting_frequency=posting_frequency,
                content_statistics=content_statistics,
            )

        except Exception as e:
            logger.error(f"Error analyzing frequency activity: {str(e)}")
            raise

    async def _analyze_kpi_performance(
        self, profile_data: Dict[str, Any]
    ) -> KPIAndPerformance:
        try:
            posts_data = profile_data["posts"]
            followers_count = profile_data.get("followers", 0)

            engagement_rate = self.client.calculate_engagement_rate(
                posts_data, followers_count
            )
            content_performance = self.client.analyze_content_performance(posts_data)

            avg_likes = content_performance.get("avg_likes", 0)
            avg_comments = content_performance.get("avg_comments", 0)

            return KPIAndPerformance(
                engagement_rate=engagement_rate,
                impressions=None,
                reach=None,
                avg_likes_per_post=avg_likes,
                avg_comments_per_post=avg_comments,
                video_views=None,
                reel_plays=None,
                view_through_rate=None,
                stories_impression_rate=None,
                bio_link_ctr=None,
                avg_reach_per_post=None,
                avg_interactions_per_post=avg_likes + avg_comments,
                follower_demographics=None,
            )

        except Exception as e:
            logger.error(f"Error analyzing KPI performance: {str(e)}")
            raise

    async def _analyze_content_format(
        self, profile_data: Dict[str, Any]
    ) -> ContentAndFormat:
        try:
            posts_data = profile_data["posts"]
            profile_info = profile_data["profile"]

            content_performance = self.client.analyze_content_performance(posts_data)
            captions = [post.get("caption", "") or "" for post in posts_data[:20]]

            collaboration_data = self.text_analyzer.detect_collaborations(captions)
            creative_style = self.text_analyzer.analyze_creative_style(
                captions, profile_data.get("biography", "")
            )

            video_count = content_performance.get("video_performance", {}).get(
                "count", 0
            )
            carousel_count = content_performance.get("carousel_performance", {}).get(
                "count", 0
            )
            image_count = content_performance.get("image_performance", {}).get(
                "count", 0
            )
            total_analyzed = content_performance.get("total_posts_analyzed", 1)

            content_types = {
                "reel": {
                    "count": video_count,
                    "percentage": round((video_count / total_analyzed) * 100, 1)
                    if total_analyzed > 0
                    else 0,
                    "avg_likes": content_performance.get("video_performance", {}).get(
                        "avg_likes", 0
                    ),
                    "collaborations": collaboration_data.get("collaboration_count", 0),
                },
                "carousel": {
                    "count": carousel_count,
                    "percentage": round((carousel_count / total_analyzed) * 100, 1)
                    if total_analyzed > 0
                    else 0,
                    "avg_likes": content_performance.get(
                        "carousel_performance", {}
                    ).get("avg_likes", 0),
                    "collaborations": collaboration_data.get("collaboration_count", 0),
                },
                "static_post": {
                    "count": image_count,
                    "percentage": round((image_count / total_analyzed) * 100, 1)
                    if total_analyzed > 0
                    else 0,
                    "avg_likes": content_performance.get("image_performance", {}).get(
                        "avg_likes", 0
                    ),
                    "collaborations": collaboration_data.get("collaboration_count", 0),
                },
            }

            best_content = []
            followers = profile_data.get("followers", 1) or 1
            for post in content_performance.get("best_posts", [])[:3]:
                engagement_rate = (
                    (post["likes"] + post["comments"]) / max(followers, 1)
                ) * 100
                best_content.append(
                    {
                        "type": post["type"],
                        "link": post["url"],
                        "likes": str(post["likes"]),
                        "comments": str(post["comments"]),
                        "engagement_rate": f"{engagement_rate:.2f}%",
                    }
                )

            return ContentAndFormat(
                content_types=content_types,
                creative_analysis=creative_style,
                best_content=best_content,
            )

        except Exception as e:
            logger.error(f"Error analyzing content format: {str(e)}")
            raise

    async def _analyze_tone_of_voice(
        self, profile_data: Dict[str, Any]
    ) -> InstagramToneOfVoice:
        try:
            posts_data = profile_data["posts"]

            captions = [
                post.get("caption", "") or ""
                for post in posts_data[:15]
                if post.get("caption")
            ]
            bio = profile_data.get("biography", "")

            if not captions and not bio:
                tone = "professionale"
            else:
                tone = self.text_analyzer.analyze_tone_of_voice(captions + [bio])

            return InstagramToneOfVoice(tone=tone)

        except Exception as e:
            logger.error(f"Error analyzing tone of voice: {str(e)}")
            raise

    async def _analyze_trends_hashtags(
        self, profile_data: Dict[str, Any]
    ) -> TrendsAndHashtags:
        try:
            posts_data = profile_data["posts"]

            hashtag_data = self.client.extract_hashtags(posts_data)

            if not hashtag_data:
                return TrendsAndHashtags(
                    active_trends=False,
                    effective_formats=False,
                    hashtag_analysis="Nessun hashtag trovato nei post analizzati",
                )

            uses_trends = hashtag_data.get("avg_hashtags_per_post", 0) > 3
            effective_formats = hashtag_data.get("unique_hashtags", 0) > 10

            analysis_parts = []
            avg_hashtags = hashtag_data.get("avg_hashtags_per_post", 0)
            total_unique = hashtag_data.get("unique_hashtags", 0)
            top_hashtags = hashtag_data.get("top_hashtags", [])[:5]

            analysis_parts.append(f"Media {avg_hashtags:.1f} hashtag per post")
            analysis_parts.append(f"{total_unique} hashtag unici utilizzati")

            if top_hashtags:
                top_names = [tag[0] for tag in top_hashtags]
                analysis_parts.append(
                    f"Hashtag più usati: #{', #'.join(top_names[:3])}"
                )

            hashtag_analysis = " | ".join(analysis_parts)

            return TrendsAndHashtags(
                active_trends=uses_trends,
                effective_formats=effective_formats,
                hashtag_analysis=hashtag_analysis,
            )

        except Exception as e:
            logger.error(f"Error analyzing trends hashtags: {str(e)}")
            raise

    async def _analyze_funnel_objectives(
        self, profile_data: Dict[str, Any]
    ) -> InstagramFunnelAndObjectives:
        try:
            posts_data = profile_data["posts"]

            captions = [
                post.get("caption", "") or ""
                for post in posts_data[:20]
                if post.get("caption")
            ]
            bio = profile_data.get("biography", "")

            objective = self.text_analyzer.analyze_profile_objective(bio, captions)
            has_ambassadors = self.text_analyzer.detect_brand_ambassadors(bio, captions)

            if profile_data.get("is_business", False) and bio:
                if any(
                    word in bio.lower() for word in ["shop", "store", "buy", "acquista"]
                ):
                    objective = "conversione"
                elif any(
                    word in bio.lower() for word in ["brand", "official", "azienda"]
                ):
                    objective = "awareness"

            return InstagramFunnelAndObjectives(
                profile_objective=objective, brand_ambassadors=has_ambassadors
            )

        except Exception as e:
            logger.error(f"Error analyzing funnel objectives: {str(e)}")
            raise
