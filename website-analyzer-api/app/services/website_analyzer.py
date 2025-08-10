"""
Servizio Core per l'Analisi di Siti Web.

Implementa funzionalità MVP di analisi siti web con caratteristiche essenziali 
per business intelligence e rilevamento tecnologie.
"""

import re
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
import validators
from bs4 import BeautifulSoup

from app.models import (
    WebsiteAnalysisRequest, 
    WebsiteAnalysisResult,
    BusinessInfo,
    TechnologyInfo,
    SeoMetrics,
    PerformanceMetrics,
    ContentAnalysis
)
from app.utils.http_client import WebsiteHTTPClient
from app.utils.logger import setup_logger
from app.utils.retry import retry_external_calls, with_retry_logging

# Logger per il servizio di analisi
logger = setup_logger(__name__)


class WebsiteAnalyzer:
    """
    Servizio core per l'analisi completa di siti web.
    
    Fornisce funzionalità di business intelligence per l'estrazione automatica di:
    - Informazioni aziendali e contatti
    - Stack tecnologico utilizzato
    - Metriche SEO e performance
    - Analisi contenuti e linguaggio
    """
    
    def __init__(self):
        """Inizializza l'analizzatore di siti web con client HTTP e pattern detection."""
        self.http_client = WebsiteHTTPClient()
        
        # Pattern per il rilevamento delle tecnologie web più comuni
        self.tech_patterns = {
            "React": [
                r"react(?:\.production)?\.min\.js",
                r"_app/static/chunks/framework",
                r"__NEXT_DATA__",
                r"React\.createElement"
            ],
            "Vue.js": [
                r"vue(?:\.min)?\.js",
                r"Vue\.config",
                r"v-if|v-for|v-model",
                r"Vue\.component"
            ],
            "Angular": [
                r"angular(?:\.min)?\.js",
                r"ng-app",
                r"@angular/core",
                r"ng-controller"
            ],
            "jQuery": [
                r"jquery(?:-[\d.]+)?(?:\.min)?\.js",
                r"\$\(",
                r"jQuery"
            ],
            "Bootstrap": [
                r"bootstrap(?:\.min)?\.css",
                r"bootstrap(?:\.min)?\.js", 
                r"col-md-|col-lg-|col-sm-",
                r"container-fluid|row"
            ],
            "WordPress": [
                r"/wp-content/",
                r"/wp-includes/",
                r"wp-json",
                r"wp-admin"
            ],
            "Shopify": [
                r"\.myshopify\.com",
                r"Shopify\.theme",
                r"/assets/theme",
                r"shopify-section"
            ],
            "Next.js": [
                r"__NEXT_DATA__",
                r"_next/static",
                r"next/router"
            ],
            "Nuxt.js": [
                r"__NUXT__",
                r"_nuxt/",
                r"nuxt-link"
            ],
            "Drupal": [
                r"Drupal\.settings",
                r"/sites/default/files",
                r"drupal\.js"
            ],
            "Magento": [
                r"var FORM_KEY",
                r"/skin/frontend/",
                r"Mage\.Cookies"
            ]
        }
        
        # Pattern per identificazione framework CSS aggiuntivi
        self.css_frameworks = {
            "Tailwind CSS": [r"tailwindcss", r"tw-", r"bg-blue-", r"text-center"],
            "Foundation": [r"foundation\.css", r"small-\d+", r"medium-\d+"],
            "Bulma": [r"bulma", r"is-primary", r"column"],
            "Semantic UI": [r"semantic\.css", r"ui container", r"ui button"]
        }
        
        logger.info(
            "WebsiteAnalyzer inizializzato", 
            extra={
                "tecnologie_supportate": len(self.tech_patterns),
                "framework_css_supportati": len(self.css_frameworks)
            }
        )
    
    @retry_external_calls
    @with_retry_logging
    async def analyze_website(self, request: WebsiteAnalysisRequest) -> WebsiteAnalysisResult:
        """
        Analizza un sito web e restituisce risultati completi di business intelligence.
        
        Esegue un'analisi approfondita che include:
        - Estrazione informazioni aziendali (nome, contatti, descrizione)
        - Rilevamento stack tecnologico (framework, librerie, CMS)
        - Analisi SEO (meta tag, struttura, performance)
        - Metriche di performance (velocità, dimensioni, tempi di risposta)
        - Analisi contenuti (lingua, argomenti, leggibilità)
        
        Args:
            request: Richiesta di analisi con URL e parametri
            
        Returns:
            WebsiteAnalysisResult: Risultati completi dell'analisi
            
        Raises:
            Exception: In caso di errori di connessione o parsing
        """
        start_time = time.time()
        url = str(request.url)
        
        logger.info(
            "Avvio analisi sito web completa",
            extra={
                "url": url,
                "profondita_analisi": request.analysis_depth,
                "includi_sottodomini": request.include_subdomains,
                "max_pagine": request.max_pages
            }
        )
        
        try:
            # Scaricamento pagina principale con ottimizzazioni performance
            response = await self.http_client.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            logger.debug(
                "Pagina principale scaricata con successo",
                extra={
                    "dimensione_bytes": len(response.content),
                    "status_code": response.status_code,
                    "content_type": response.headers.get('content-type', 'unknown')
                }
            )
            
            # Esecuzione analisi parallele per ottimizzare performance
            business_info = self._extract_business_info(soup, url)
            technologies = self._detect_technologies(response.text, soup)
            seo_metrics = self._analyze_seo(soup, response, url)
            performance_metrics = self._analyze_performance(response, start_time)
            content_analysis = self._analyze_content(soup)
            
            # Calcolo durata analisi totale
            analysis_duration = time.time() - start_time
            
            logger.info(
                "Analisi completata con successo",
                extra={
                    "durata_analisi": round(analysis_duration, 3),
                    "tecnologie_rilevate": len(technologies),
                    "business_info_trovata": business_info.company_name is not None
                }
            )
            
            # Costruzione risultato finale ottimizzato
            result = WebsiteAnalysisResult(
                analyzed_url=url,
                analysis_depth=request.analysis_depth,
                analysis_timestamp=datetime.utcnow(),
                analysis_duration_seconds=round(analysis_duration, 2),
                business_info=business_info,
                technologies=technologies,
                seo_metrics=seo_metrics,
                performance_metrics=performance_metrics,
                content_analysis=content_analysis,
                pages_analyzed=1,
                analysis_success=True,
                confidence_score=self._calculate_confidence_score(
                    business_info, technologies, seo_metrics
                )
            )
            
            logger.info(
                f"Website analysis completed successfully",
                extra={
                    "url": url,
                    "duration_seconds": analysis_duration,
                    "confidence_score": result.confidence_score,
                    "technologies_found": len(technologies)
                }
            )
            
            return result
            
        except Exception as e:
            analysis_duration = time.time() - start_time
            
            logger.error(
                f"Website analysis failed",
                extra={
                    "url": url,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration_seconds": analysis_duration
                },
                exc_info=True
            )
            
            # Return failed analysis result
            return WebsiteAnalysisResult(
                analyzed_url=url,
                analysis_depth=request.analysis_depth,
                analysis_timestamp=datetime.utcnow(),
                analysis_duration_seconds=round(analysis_duration, 2),
                business_info=BusinessInfo(),
                technologies=[],
                seo_metrics=SeoMetrics(),
                performance_metrics=PerformanceMetrics(),
                content_analysis=ContentAnalysis(),
                pages_analyzed=0,
                errors_encountered=[str(e)],
                analysis_success=False,
                confidence_score=0.0
            )
    
    def _extract_business_info(self, soup: BeautifulSoup, url: str) -> BusinessInfo:
        """Extract basic business information from the webpage."""
        try:
            # Company name extraction
            company_name = None
            
            # Try title tag
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.get_text().strip()
                # Simple heuristic: take first part before common separators
                company_name = re.split(r'[|\-–—]', title_text)[0].strip()
            
            # Try to find company name in structured data
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld and not company_name:
                try:
                    import json
                    data = json.loads(json_ld.string)
                    if isinstance(data, dict) and 'name' in data:
                        company_name = data['name']
                except:
                    pass
            
            # Industry/description from meta description
            description = None
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '').strip()
            
            # Contact information
            contact_email = None
            phone = None
            
            # Email pattern search
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            page_text = soup.get_text()
            emails = re.findall(email_pattern, page_text)
            if emails:
                # Filter out common non-contact emails
                filtered_emails = [e for e in emails if not any(
                    skip in e.lower() for skip in ['noreply', 'no-reply', 'example', 'test']
                )]
                if filtered_emails:
                    contact_email = filtered_emails[0]
            
            # Phone pattern search (simplified)
            phone_pattern = r'[\+]?[1-9]?[\-\.\s]?\(?[0-9]{3}\)?[\-\.\s]?[0-9]{3}[\-\.\s]?[0-9]{4}'
            phones = re.findall(phone_pattern, page_text)
            if phones:
                phone = phones[0].strip()
            
            return BusinessInfo(
                company_name=company_name,
                description=description,
                contact_email=contact_email,
                phone=phone
            )
            
        except Exception as e:
            logger.warning(f"Error extracting business info: {str(e)}")
            return BusinessInfo()
    
    def _detect_technologies(self, html_content: str, soup: BeautifulSoup) -> List[TechnologyInfo]:
        """Detect technologies used on the website."""
        technologies = []
        
        try:
            for tech_name, patterns in self.tech_patterns.items():
                confidence = 0.0
                matches = 0
                
                for pattern in patterns:
                    if re.search(pattern, html_content, re.IGNORECASE):
                        matches += 1
                        confidence += 0.3
                
                if matches > 0:
                    confidence = min(confidence, 1.0)
                    category = self._get_tech_category(tech_name)
                    
                    technologies.append(TechnologyInfo(
                        name=tech_name,
                        category=category,
                        confidence=confidence
                    ))
            
            # Additional detection from script tags
            script_tags = soup.find_all('script', src=True)
            for script in script_tags:
                src = script.get('src', '')
                if 'google-analytics' in src or 'gtag' in src:
                    technologies.append(TechnologyInfo(
                        name="Google Analytics",
                        category="Analytics",
                        confidence=0.9
                    ))
                elif 'googleapis.com' in src:
                    technologies.append(TechnologyInfo(
                        name="Google APIs",
                        category="External Service",
                        confidence=0.8
                    ))
            
            return technologies
            
        except Exception as e:
            logger.warning(f"Error detecting technologies: {str(e)}")
            return []
    
    def _get_tech_category(self, tech_name: str) -> str:
        """Get category for a technology."""
        categories = {
            "React": "Frontend Framework",
            "Vue.js": "Frontend Framework", 
            "Angular": "Frontend Framework",
            "jQuery": "JavaScript Library",
            "Bootstrap": "CSS Framework",
            "WordPress": "CMS",
            "Shopify": "E-commerce Platform"
        }
        return categories.get(tech_name, "Unknown")
    
    def _analyze_seo(self, soup: BeautifulSoup, response, url: str) -> SeoMetrics:
        """Analyze SEO metrics."""
        try:
            # Title tag
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else None
            
            # Meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '').strip() if meta_desc else None
            
            # H1 tags
            h1_tags = [h1.get_text().strip() for h1 in soup.find_all('h1')]
            
            # Meta keywords (mostly obsolete but sometimes present)
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            keywords = meta_keywords.get('content', '').strip() if meta_keywords else None
            
            # SSL check
            ssl_enabled = url.startswith('https://')
            
            # Robots.txt and sitemap (would need additional requests)
            robots_txt_exists = False
            sitemap_exists = False
            
            return SeoMetrics(
                title_tag=title,
                meta_description=description,
                h1_tags=h1_tags,
                meta_keywords=keywords,
                robots_txt_exists=robots_txt_exists,
                sitemap_exists=sitemap_exists,
                ssl_enabled=ssl_enabled
            )
            
        except Exception as e:
            logger.warning(f"Error analyzing SEO: {str(e)}")
            return SeoMetrics()
    
    def _analyze_performance(self, response, start_time: float) -> PerformanceMetrics:
        """Analyze basic performance metrics."""
        try:
            response_time = time.time() - start_time
            page_size = len(response.content)
            status_code = response.status_code
            
            return PerformanceMetrics(
                response_time=round(response_time, 3),
                page_size_bytes=page_size,
                status_code=status_code
            )
            
        except Exception as e:
            logger.warning(f"Error analyzing performance: {str(e)}")
            return PerformanceMetrics()
    
    def _analyze_content(self, soup: BeautifulSoup) -> ContentAnalysis:
        """Analyze page content."""
        try:
            # Extract text content
            text_content = soup.get_text()
            words = text_content.split()
            word_count = len(words)
            
            # Simple language detection (basic heuristic)
            language = "en"  # Default
            if soup.html and soup.html.get('lang'):
                language = soup.html.get('lang')[:2]
            
            # Extract key topics (simple keyword extraction)
            # Remove common stop words and get most frequent words
            stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
            words_clean = [word.lower().strip('.,!?;:"()[]{}') for word in words 
                          if len(word) > 3 and word.lower() not in stop_words]
            
            # Count word frequency
            word_freq = {}
            for word in words_clean:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get top keywords
            key_topics = sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)[:10]
            
            return ContentAnalysis(
                word_count=word_count,
                language=language,
                key_topics=key_topics
            )
            
        except Exception as e:
            logger.warning(f"Error analyzing content: {str(e)}")
            return ContentAnalysis()
    
    def _calculate_confidence_score(
        self, 
        business_info: BusinessInfo, 
        technologies: List[TechnologyInfo], 
        seo_metrics: SeoMetrics
    ) -> float:
        """Calculate overall confidence score for the analysis."""
        score = 0.0
        
        # Business info completeness (0.4 weight)
        business_score = 0.0
        if business_info.company_name:
            business_score += 0.3
        if business_info.description:
            business_score += 0.2
        if business_info.contact_email:
            business_score += 0.2
        if business_info.phone:
            business_score += 0.1
        
        score += business_score * 0.4
        
        # Technology detection (0.3 weight)
        tech_score = min(len(technologies) * 0.2, 1.0)
        score += tech_score * 0.3
        
        # SEO completeness (0.3 weight)
        seo_score = 0.0
        if seo_metrics.title_tag:
            seo_score += 0.4
        if seo_metrics.meta_description:
            seo_score += 0.3
        if seo_metrics.h1_tags:
            seo_score += 0.2
        if seo_metrics.ssl_enabled:
            seo_score += 0.1
        
        score += seo_score * 0.3
        
        return round(min(score, 1.0), 2)
