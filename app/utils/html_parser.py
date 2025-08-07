from typing import List, Dict, Optional
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse
import re


class HTMLParser:
    """Utility per il parsing e l'analisi di HTML"""
    
    def __init__(self, html: str, base_url: str = ""):
        self.soup = BeautifulSoup(html, "lxml")
        self.base_url = base_url
    
    def get_title(self) -> Optional[str]:
        """Estrae il titolo della pagina"""
        title = self.soup.find("title")
        return title.text.strip() if title else None
    
    def get_meta_description(self) -> Optional[str]:
        """Estrae la meta description"""
        meta = self.soup.find("meta", attrs={"name": "description"})
        return meta.get("content", "").strip() if meta else None
    
    def get_all_links(self) -> List[Dict[str, str]]:
        """Estrae tutti i link dalla pagina"""
        links = []
        for link in self.soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)
            absolute_url = urljoin(self.base_url, href)
            
            links.append({
                "url": absolute_url,
                "text": text,
                "is_internal": self._is_internal_link(absolute_url)
            })
        
        return links
    
    def get_headings(self) -> Dict[str, List[str]]:
        """Estrae tutti gli heading (h1-h6) dalla pagina"""
        headings = {}
        for i in range(1, 7):
            h_tags = self.soup.find_all(f"h{i}")
            if h_tags:
                headings[f"h{i}"] = [tag.get_text(strip=True) for tag in h_tags]
        
        return headings
    
    def get_images(self) -> List[Dict[str, Optional[str]]]:
        """Estrae tutte le immagini con relativi attributi"""
        images = []
        for img in self.soup.find_all("img"):
            images.append({
                "src": urljoin(self.base_url, img.get("src", "")),
                "alt": img.get("alt", ""),
                "title": img.get("title", "")
            })
        
        return images
    
    def get_navigation_elements(self) -> List[str]:
        """Identifica elementi di navigazione"""
        nav_elements = []
        
        # Cerca nav tags
        for nav in self.soup.find_all("nav"):
            nav_elements.extend([
                link.get_text(strip=True) 
                for link in nav.find_all("a", href=True)
            ])
        
        # Cerca menu comuni
        for selector in ["#menu", ".menu", "#navigation", ".navigation"]:
            elements = self.soup.select(selector)
            for elem in elements:
                nav_elements.extend([
                    link.get_text(strip=True) 
                    for link in elem.find_all("a", href=True)
                ])
        
        return list(set(nav_elements))
    
    def detect_cta_buttons(self) -> List[str]:
        """Identifica possibili Call-To-Action"""
        cta_keywords = [
            "buy", "purchase", "shop", "add to cart", "checkout",
            "subscribe", "sign up", "register", "download", "get started",
            "contact", "learn more", "try", "demo"
        ]
        
        ctas = []
        
        # Cerca button e link con testo CTA
        for elem in self.soup.find_all(["button", "a"]):
            text = elem.get_text(strip=True).lower()
            if any(keyword in text for keyword in cta_keywords):
                ctas.append(elem.get_text(strip=True))
        
        return list(set(ctas))
    
    def _is_internal_link(self, url: str) -> bool:
        """Verifica se un link è interno al dominio base"""
        if not self.base_url:
            return True
        
        base_domain = urlparse(self.base_url).netloc
        link_domain = urlparse(url).netloc
        
        return link_domain == base_domain or link_domain == ""