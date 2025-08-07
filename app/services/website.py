from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse, urljoin
import asyncio
import re

from app.models.website import (
    WebsiteScrapingResult,
    SiteStructure,
    NavigationAndLanding,
    FunnelAndObjectives,
    ToneOfVoice,
    UserExperience
)
from app.utils import HTTPClient, HTMLParser, setup_logger

logger = setup_logger(__name__)


class WebsiteScraper:
    """Servizio per lo scraping e l'analisi di siti web"""
    
    def __init__(self):
        self.http_client = HTTPClient()
    
    async def scrape(self, url: str) -> WebsiteScrapingResult:
        """
        Esegue lo scraping completo di un sito web
        """
        try:
            logger.info(f"Starting website scraping for: {url}")
            
            # Fetch della homepage
            response = await self.http_client.get(url)
            html_content = response.text
            
            # Parse HTML
            parser = HTMLParser(html_content, url)
            
            # Analisi parallela di varie metriche
            results = await asyncio.gather(
                self._analyze_site_structure(parser, url),
                self._analyze_navigation_and_landing(parser),
                self._analyze_funnel_and_objectives(parser),
                self._analyze_tone_of_voice(parser),
                self._analyze_user_experience(parser, url),
                return_exceptions=True
            )
            
            # Costruzione risultato
            result = WebsiteScrapingResult(
                url=url,
                scraping_date=datetime.utcnow().isoformat(),
                site_structure=results[0] if not isinstance(results[0], Exception) else SiteStructure(),
                navigation_landing=results[1] if not isinstance(results[1], Exception) else NavigationAndLanding(),
                funnel_objectives=results[2] if not isinstance(results[2], Exception) else FunnelAndObjectives(),
                tone_of_voice=results[3] if not isinstance(results[3], Exception) else ToneOfVoice(),
                user_experience=results[4] if not isinstance(results[4], Exception) else UserExperience()
            )
            
            logger.info(f"Website scraping completed for: {url}")
            return result
            
        except Exception as e:
            logger.error(f"Error scraping website {url}: {str(e)}")
            return WebsiteScrapingResult(
                url=url,
                scraping_date=datetime.utcnow().isoformat(),
                error_message=str(e)
            )
    
    async def _analyze_site_structure(self, parser: HTMLParser, base_url: str) -> SiteStructure:
        """Analizza la struttura del sito"""
        try:
            # Analisi dei link interni
            all_links = parser.get_all_links()
            internal_links = [link["url"] for link in all_links if link["is_internal"]]
            
            # Identifica sezioni principali dal menu di navigazione
            nav_elements = parser.get_navigation_elements()
            
            # Stima profondità navigazione (basata su livelli di URL)
            navigation_depth = max([
                len(urlparse(link).path.strip('/').split('/')) 
                for link in internal_links[:20]
            ] + [1])
            
            # Identifica possibili errori SEO
            seo_errors = []
            
            # Controlla title duplicati o mancanti
            title = parser.get_title()
            if not title:
                seo_errors.append("title mancante")
            elif len(title) > 60:
                seo_errors.append("title troppo lungo")
            
            # Controlla meta description
            meta_desc = parser.get_meta_description()
            if not meta_desc:
                seo_errors.append("meta description mancante")
            
            # Controlla heading structure
            headings = parser.get_headings()
            if not headings.get("h1"):
                seo_errors.append("h1 mancante")
            elif len(headings.get("h1", [])) > 1:
                seo_errors.append("h1 multipli")
            
            return SiteStructure(
                structure_analysis=nav_elements[:10] if nav_elements else ["homepage", "prodotti", "contatti"],
                navigation_depth=min(navigation_depth, 5),
                internal_links=[link.replace(base_url, "") for link in internal_links[:10]],
                seo_errors=seo_errors if seo_errors else ["nessun errore rilevato"]
            )
        except Exception as e:
            logger.error(f"Error analyzing site structure: {str(e)}")
            return SiteStructure()
    
    async def _analyze_navigation_and_landing(self, parser: HTMLParser) -> NavigationAndLanding:
        """Analizza navigazione e landing pages"""
        try:
            # Analisi CTA e link
            all_links = parser.get_all_links()
            internal_links_count = sum(1 for link in all_links if link["is_internal"])
            external_links = any(not link["is_internal"] for link in all_links)
            
            # Identifica CTA
            ctas = parser.detect_cta_buttons()
            
            # Analisi top pages (simulata da link più frequenti)
            link_texts = [link["text"] for link in all_links if link["text"]]
            top_pages = list(set(link_texts))[:5]
            
            return NavigationAndLanding(
                user_sources=["organic", "direct", "social"],  # Dummy data
                internal_links_cta=internal_links_count + len(ctas),
                external_links_collaborations=external_links,
                bounce_rate=45.2,  # Dummy data
                session_duration=156.8,  # Dummy data
                top_pages=[f"/{page.lower().replace(' ', '-')}" for page in top_pages]
            )
        except Exception as e:
            logger.error(f"Error analyzing navigation: {str(e)}")
            return NavigationAndLanding()
    
    async def _analyze_funnel_and_objectives(self, parser: HTMLParser) -> FunnelAndObjectives:
        """Analizza funnel e obiettivi del sito"""
        try:
            # Identifica obiettivo principale basandosi su CTA e contenuti
            ctas = parser.detect_cta_buttons()
            cta_text = " ".join(ctas).lower()
            
            # Determina obiettivo principale
            if any(word in cta_text for word in ["buy", "purchase", "cart", "checkout"]):
                main_objective = "vendita"
                funnel_phase = "conversion"
            elif any(word in cta_text for word in ["subscribe", "newsletter", "download"]):
                main_objective = "posizionamento"
                funnel_phase = "consideration"
            else:
                main_objective = "posizionamento"
                funnel_phase = "awareness"
            
            # Analisi del funnel implicito
            implicit_funnel = self._detect_implicit_funnel(parser)
            
            return FunnelAndObjectives(
                funnel_phase=funnel_phase,
                main_objective=main_objective,
                implicit_funnel=implicit_funnel
            )
        except Exception as e:
            logger.error(f"Error analyzing funnel: {str(e)}")
            return FunnelAndObjectives()
    
    async def _analyze_tone_of_voice(self, parser: HTMLParser) -> ToneOfVoice:
        """Analizza il tone of voice del sito"""
        try:
            # Analisi del contenuto testuale per determinare lo stile
            body_text = parser.soup.get_text(separator=' ', strip=True)
            
            # Rimuovi script e style
            for script in parser.soup(["script", "style"]):
                script.decompose()
            
            # Analisi keywords per stile
            premium_keywords = ["esclusivo", "premium", "luxury", "elegante", "raffinato"]
            professional_keywords = ["professionale", "affidabile", "competenza", "esperienza"]
            casual_keywords = ["semplice", "facile", "veloce", "pratico"]
            
            text_lower = body_text.lower()
            
            if any(keyword in text_lower for keyword in premium_keywords):
                perceived_style = "premium"
            elif any(keyword in text_lower for keyword in professional_keywords):
                perceived_style = "professionale"
            elif any(keyword in text_lower for keyword in casual_keywords):
                perceived_style = "casual"
            else:
                perceived_style = "minimale"
            
            return ToneOfVoice(
                social_site_coherence=True,  # Dummy data
                perceived_style=perceived_style
            )
        except Exception as e:
            logger.error(f"Error analyzing tone of voice: {str(e)}")
            return ToneOfVoice()
    
    async def _analyze_user_experience(self, parser: HTMLParser, url: str) -> UserExperience:
        """Analizza l'esperienza utente del sito"""
        try:
            # Analisi navigazione (basata su presenza menu e struttura)
            nav_elements = parser.get_navigation_elements()
            navigation_quality = "ottima" if len(nav_elements) > 5 else "buona"
            
            # Analisi design (basata su presenza di elementi moderni)
            images = parser.get_images()
            has_images = len(images) > 0
            
            # Check responsive meta tag
            viewport_meta = parser.soup.find("meta", attrs={"name": "viewport"})
            is_responsive = viewport_meta is not None
            
            if is_responsive and has_images:
                design_quality = "moderno"
            elif is_responsive:
                design_quality = "minimale"
            else:
                design_quality = "classico"
            
            # Performance simulata (in produzione si userebbero tool esterni)
            performance_metrics = [
                {"LCP": "1850ms"},  # Largest Contentful Paint
                {"FID": "55ms"},    # First Input Delay
                {"CLS": "0.09"}     # Cumulative Layout Shift
            ]
            
            return UserExperience(
                navigation_fluidity=navigation_quality,
                perceived_design=design_quality,
                technical_performance=performance_metrics
            )
        except Exception as e:
            logger.error(f"Error analyzing UX: {str(e)}")
            return UserExperience()
    
    def _detect_implicit_funnel(self, parser: HTMLParser) -> str:
        """Identifica il funnel implicito dal comportamento del sito"""
        ctas = parser.detect_cta_buttons()
        
        if any("cart" in cta.lower() or "checkout" in cta.lower() for cta in ctas):
            return "homepage > catalogo prodotti > dettaglio prodotto > carrello > checkout"
        elif any("contact" in cta.lower() for cta in ctas):
            return "homepage > servizi > chi siamo > contatti"
        elif any("download" in cta.lower() for cta in ctas):
            return "homepage > risorse > download"
        else:
            return "homepage > esplorazione contenuti > azione finale"