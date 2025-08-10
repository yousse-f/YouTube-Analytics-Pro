"""
Pydantic models for Website Analyzer API.

Data models for requests, responses, and business entities.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, field_validator, ConfigDict
from enum import Enum


class AnalysisDepth(str, Enum):
    """Analysis depth levels."""
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


class WebsiteAnalysisRequest(BaseModel):
    """Request model for website analysis."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://example.com",
                "analysis_depth": "standard",
                "include_subdomains": False,
                "max_pages": 5
            }
        }
    )
    
    url: HttpUrl
    analysis_depth: AnalysisDepth = AnalysisDepth.STANDARD
    include_subdomains: bool = False
    max_pages: Optional[int] = None


class TechnologyInfo(BaseModel):
    """Technology information detected on the website."""
    name: str
    category: str
    version: Optional[str] = None
    confidence: float  # 0.0 to 1.0


class BusinessInfo(BaseModel):
    """Basic business information extracted from website."""
    company_name: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class SeoMetrics(BaseModel):
    """SEO metrics and analysis."""
    title_tag: Optional[str] = None
    meta_description: Optional[str] = None
    h1_tags: List[str] = []
    meta_keywords: Optional[str] = None
    robots_txt_exists: bool = False
    sitemap_exists: bool = False
    ssl_enabled: bool = False


class PerformanceMetrics(BaseModel):
    """Website performance metrics."""
    page_load_time: Optional[float] = None
    page_size_bytes: Optional[int] = None
    response_time: Optional[float] = None
    status_code: Optional[int] = None


class ContentAnalysis(BaseModel):
    """Content analysis results."""
    word_count: int = 0
    language: Optional[str] = None
    readability_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    key_topics: List[str] = []


class WebsiteAnalysisResult(BaseModel):
    """Complete website analysis result."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "analyzed_url": "https://example.com",
                "analysis_depth": "standard",
                "analysis_timestamp": "2025-08-10T14:30:00Z",
                "analysis_duration_seconds": 15.5,
                "business_info": {
                    "company_name": "Example Corp",
                    "industry": "Technology",
                    "description": "Leading tech company"
                },
                "technologies": [
                    {
                        "name": "React",
                        "category": "Frontend Framework",
                        "version": "18.2.0",
                        "confidence": 0.95
                    }
                ],
                "seo_metrics": {
                    "title_tag": "Example Corp - Leading Technology Solutions",
                    "ssl_enabled": True
                },
                "analysis_success": True,
                "confidence_score": 0.85
            }
        }
    )
    
    # Request metadata
    analyzed_url: str
    analysis_depth: str
    analysis_timestamp: datetime
    analysis_duration_seconds: float
    
    # Core analysis results
    business_info: BusinessInfo
    technologies: List[TechnologyInfo]
    seo_metrics: SeoMetrics
    performance_metrics: PerformanceMetrics
    content_analysis: ContentAnalysis
    
    # Additional data
    pages_analyzed: int
    errors_encountered: List[str] = []
    warnings: List[str] = []
    
    # Success indicators
    analysis_success: bool = True
    confidence_score: float = 0.0  # Overall confidence in analysis


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "timestamp": "2025-08-10T14:30:00Z",
                "version": "1.0.0",
                "uptime_seconds": 3600.0
            }
        }
    )
    
    status: str = "healthy"
    timestamp: datetime
    version: str
    uptime_seconds: float


class ErrorResponse(BaseModel):
    """Standard error response model."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Analysis Failed",
                "detail": "Unable to access the provided URL",
                "timestamp": "2025-08-10T14:30:00Z",
                "request_id": "abc123"
            }
        }
    )
    
    error: str
    detail: str
    timestamp: datetime
    request_id: Optional[str] = None
