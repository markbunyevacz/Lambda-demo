"""
Rockwool Scraper - Rockwool.hu weboldal automatizált adatgyűjtés

Ez az osztály kezeli a teljes Rockwool weboldal scraping folyamatát:
1. Weboldal térképezés és navigációs szerkezet feltárása
2. Terméklisták azonosítása és bejárása
3. Termékadatok részletes kinyerése
4. Műszaki adatlapok letöltése és feldolgozása
5. Képek és dokumentumok mentése
"""

import requests
import time
import logging
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from dataclasses import dataclass
import json
import os
from datetime import datetime

from .product_parser import ProductParser
from .category_mapper import CategoryMapper
from .data_validator import DataValidator

logger = logging.getLogger(__name__)

@dataclass
class ScrapingConfig:
    """Scraping konfigurációs beállítások"""
    base_url: str = "https://www.rockwool.hu"
    max_requests_per_minute: int = 30
    request_delay: float = 2.0
    timeout: int = 30
    max_retries: int = 3
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
@dataclass
class ScrapedProduct:
    """Scraped termék adatstruktúra"""
    name: str
    url: str
    category: str
    description: str
    technical_specs: Dict
    images: List[str]
    documents: List[str]
    price: Optional[float] = None
    availability: bool = True
    scraped_at: datetime = None

class RockwoolScraper:
    """
    Rockwool weboldal scraper osztály
    
    Funkcionalitás:
    - Weboldal struktúra elemzése
    - Termékek automatikus felderítése
    - Részletes termékadatok kinyerése
    - Műszaki adatlapok feldolgozása
    - Rate limiting és error handling
    """
    
    def __init__(self, config: ScrapingConfig = None):
        self.config = config or ScrapingConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'hu-HU,hu;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        self.product_parser = ProductParser()
        self.category_mapper = CategoryMapper()
        self.data_validator = DataValidator()
        
        # Scraping állapot nyomon követése
        self.scraped_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.last_request_time: float = 0
        
        logger.info(f"RockwoolScraper inicializálva: {self.config.base_url}")
    
    def _rate_limit(self):
        """Rate limiting - késleltetés kérések között"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.config.request_delay:
            sleep_time = self.config.request_delay - time_since_last
            logger.debug(f"Rate limiting: várakozás {sleep_time:.2f} másodperc")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _fetch_page(self, url: str, retries: int = None) -> Optional[BeautifulSoup]:
        """
        Biztonságos oldal letöltés retry logikával
        
        Args:
            url: Lekérni kívánt URL
            retries: Újrapróbálkozások száma
            
        Returns:
            BeautifulSoup objektum vagy None hiba esetén
        """
        if retries is None:
            retries = self.config.max_retries
            
        self._rate_limit()
        
        for attempt in range(retries + 1):
            try:
                logger.debug(f"Oldal letöltése: {url} (kísérlet {attempt + 1}/{retries + 1})")
                
                response = self.session.get(
                    url, 
                    timeout=self.config.timeout,
                    allow_redirects=True
                )
                response.raise_for_status()
                
                # Encoding ellenőrzése és beállítása
                if response.encoding != 'utf-8':
                    response.encoding = 'utf-8'
                
                soup = BeautifulSoup(response.content, 'html.parser')
                logger.debug(f"Sikeres letöltés: {url}")
                return soup
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Hiba az oldal letöltésénél {url}: {e}")
                if attempt < retries:
                    wait_time = (attempt + 1) * 2
                    logger.info(f"Újrapróbálkozás {wait_time} másodperc múlva...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Végleg sikertelen: {url}")
                    self.failed_urls.add(url)
                    return None
        
        return None
    
    def discover_website_structure(self) -> Dict[str, List[str]]:
        """
        Weboldal struktúrájának feltérképezése
        
        Returns:
            Dict kategóriák és URL-ek listájával
        """
        logger.info("Rockwool weboldal struktúrájának feltérképezése...")
        
        structure = {
            'categories': [],
            'product_pages': [],
            'technical_pages': []
        }
        
        # Főoldal elemzése
        main_page = self._fetch_page(self.config.base_url)
        if not main_page:
            logger.error("Nem sikerült betölteni a főoldalt")
            return structure
        
        # Navigációs menü elemzése
        nav_links = self._extract_navigation_links(main_page)
        logger.info(f"Talált navigációs linkek: {len(nav_links)}")
        
        # Termék kategóriák azonosítása
        category_links = self._find_category_links(main_page)
        structure['categories'] = category_links
        
        # Termékadatlap oldalak keresése  
        product_links = self._find_product_links(main_page)
        structure['product_pages'] = product_links
        
        logger.info(f"Weboldal struktúra feltérképezve: {len(structure['categories'])} kategória, {len(structure['product_pages'])} termék")
        return structure
    
    def _extract_navigation_links(self, soup: BeautifulSoup) -> List[str]:
        """Navigációs linkek kinyerése"""
        links = []
        
        # Főmenü linkek
        nav_menus = soup.find_all(['nav', 'ul'], class_=lambda x: x and ('nav' in x.lower() or 'menu' in x.lower()))
        
        for menu in nav_menus:
            menu_links = menu.find_all('a', href=True)
            for link in menu_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.config.base_url, href)
                    if self._is_rockwool_url(full_url):
                        links.append(full_url)
        
        return list(set(links))  # Duplikátumok eltávolítása
    
    def _find_category_links(self, soup: BeautifulSoup) -> List[str]:
        """Termék kategória linkek azonosítása"""
        category_links = []
        
        # "Termékek, megoldások" menüpont alatti linkek keresése
        product_menu_keywords = ['termék', 'szigetelés', 'hőszigetelés', 'hangszigetelés']
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True).lower()
            
            # Kategória linkek azonosítása szöveg alapján
            if any(keyword in text for keyword in product_menu_keywords):
                full_url = urljoin(self.config.base_url, href)
                if self._is_rockwool_url(full_url) and full_url not in category_links:
                    category_links.append(full_url)
        
        return category_links
    
    def _find_product_links(self, soup: BeautifulSoup) -> List[str]:
        """Termék specifikus linkek keresése"""
        product_links = []
        
        # Termék oldalak jellemzői alapján azonosítás
        product_indicators = [
            'multirock', 'frontrock', 'deltarock', 'airrock', 
            'steprock', 'roofrock', 'hardrock', 'termekek'
        ]
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '').lower()
            
            if any(indicator in href for indicator in product_indicators):
                full_url = urljoin(self.config.base_url, link.get('href'))
                if self._is_rockwool_url(full_url):
                    product_links.append(full_url)
        
        return list(set(product_links))
    
    def _is_rockwool_url(self, url: str) -> bool:
        """Ellenőrzi, hogy az URL a Rockwool domain-hez tartozik-e"""
        parsed = urlparse(url)
        return 'rockwool.hu' in parsed.netloc.lower()
    
    def scrape_all_products(self) -> List[ScrapedProduct]:
        """
        Összes termék adatainak legyűjtése
        
        Returns:
            Lista a scraped termékekkel
        """
        logger.info("Rockwool termékek scraping indítása...")
        
        # Weboldal struktúra feltérképezése
        structure = self.discover_website_structure()
        
        all_products = []
        
        # Kategóriánként termékek összegyűjtése
        for category_url in structure['categories']:
            logger.info(f"Kategória feldolgozása: {category_url}")
            
            category_products = self._scrape_category_products(category_url)
            all_products.extend(category_products)
            
            # Rate limiting kategóriák között
            time.sleep(1)
        
        # Direkt termék oldalak feldolgozása
        for product_url in structure['product_pages']:
            if product_url not in self.scraped_urls:
                logger.info(f"Termék feldolgozása: {product_url}")
                
                product = self._scrape_single_product(product_url)
                if product:
                    all_products.append(product)
        
        logger.info(f"Scraping befejezve: {len(all_products)} termék összegyűjtve")
        return all_products
    
    def _scrape_category_products(self, category_url: str) -> List[ScrapedProduct]:
        """Egy kategória összes termékének scraping-je"""
        products = []
        
        soup = self._fetch_page(category_url)
        if not soup:
            return products
        
        # Termék linkek keresése a kategória oldalon
        product_links = self._extract_product_links_from_page(soup)
        
        for product_url in product_links:
            if product_url not in self.scraped_urls:
                product = self._scrape_single_product(product_url)
                if product:
                    products.append(product)
                    
                # Rate limiting termékek között
                time.sleep(0.5)
        
        return products
    
    def _extract_product_links_from_page(self, soup: BeautifulSoup) -> List[str]:
        """Termék linkek kinyerése egy oldalról"""
        links = []
        
        # Különböző szelektorok termék linkekhez
        selectors = [
            'a[href*="termek"]',
            'a[href*="product"]', 
            '.product-link',
            '.termek-link',
            'a[href*="multirock"]',
            'a[href*="frontrock"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href:
                    full_url = urljoin(self.config.base_url, href)
                    if self._is_rockwool_url(full_url):
                        links.append(full_url)
        
        return list(set(links))
    
    def _scrape_single_product(self, product_url: str) -> Optional[ScrapedProduct]:
        """
        Egyetlen termék részletes adatainak scraping-je
        
        Args:
            product_url: Termék oldal URL-je
            
        Returns:
            ScrapedProduct objektum vagy None
        """
        if product_url in self.scraped_urls:
            logger.debug(f"Termék már scraping-elve: {product_url}")
            return None
        
        logger.debug(f"Termék scraping: {product_url}")
        
        soup = self._fetch_page(product_url)
        if not soup:
            return None
        
        try:
            # Alapadatok kinyerése
            product_data = self.product_parser.parse_product_page(soup, product_url)
            
            # Kategória meghatározása
            category = self.category_mapper.map_category(product_data.get('category', ''), product_url)
            
            # Műszaki specifikációk feldolgozása
            technical_specs = self.product_parser.extract_technical_specifications(soup)
            
            # Képek és dokumentumok
            images = self.product_parser.extract_images(soup, self.config.base_url)
            documents = self.product_parser.extract_documents(soup, self.config.base_url)
            
            # ScrapedProduct objektum létrehozása
            product = ScrapedProduct(
                name=product_data.get('name', ''),
                url=product_url,
                category=category,
                description=product_data.get('description', ''),
                technical_specs=technical_specs,
                images=images,
                documents=documents,
                price=product_data.get('price'),
                availability=product_data.get('availability', True),
                scraped_at=datetime.now()
            )
            
            # Adatok validálása
            if self.data_validator.validate_product(product):
                self.scraped_urls.add(product_url)
                logger.debug(f"Termék sikeresen scraping-elve: {product.name}")
                return product
            else:
                logger.warning(f"Termék validálás sikertelen: {product_url}")
                return None
                
        except Exception as e:
            logger.error(f"Hiba a termék scraping során {product_url}: {e}")
            return None
    
    def get_scraping_statistics(self) -> Dict[str, int]:
        """Scraping statisztikák lekérése"""
        return {
            'scraped_urls': len(self.scraped_urls),
            'failed_urls': len(self.failed_urls),
            'total_processed': len(self.scraped_urls) + len(self.failed_urls)
        }
    
    def save_failed_urls(self, filepath: str):
        """Sikertelen URL-ek mentése fájlba későbbi feldolgozásra"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(list(self.failed_urls), f, indent=2, ensure_ascii=False)
        logger.info(f"Sikertelen URL-ek mentve: {filepath}") 