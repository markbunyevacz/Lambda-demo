"""
Rockwool Scraper - Rockwool.hu weboldal automatizált adatgyűjtés

Ez az osztály kezeli a teljes Rockwool weboldal scraping folyamatát:
1. Weboldal térképezés és navigációs szerkezet feltárása
2. Terméklisták azonosítása és bejárása
3. Termékadatok részletes kinyerése
4. Műszaki adatlapok letöltése és feldolgozása
5. Képek és dokumentumok mentése
"""

import asyncio
import time
import logging
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from dataclasses import dataclass
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright, Browser, Page

from .product_parser import ProductParser
from .category_mapper import CategoryMapper
from .data_validator import DataValidator

logger = logging.getLogger(__name__)

@dataclass
class ScrapingConfig:
    """Scraping konfigurációs beállítások"""
    base_url: str = "https://www.rockwool.com/hu/"
    max_requests_per_minute: int = 30
    request_delay: float = 2.0
    timeout: int = 30
    max_retries: int = 3
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    headless: bool = True
    
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
    Rockwool weboldal scraper osztály - Playwright alapú
    
    Funkcionalitás:
    - Weboldal struktúra elemzése
    - Termékek automatikus felderítése
    - Részletes termékadatok kinyerése
    - Műszaki adatlapok feldolgozása
    - Rate limiting és error handling
    - JavaScript-rendered content támogatás
    """
    
    def __init__(self, config: ScrapingConfig = None):
        self.config = config or ScrapingConfig()
        self.browser: Optional[Browser] = None
        self.context = None
        
        self.product_parser = ProductParser()
        self.category_mapper = CategoryMapper()
        self.data_validator = DataValidator()
        
        # Scraping állapot nyomon követése
        self.scraped_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.last_request_time: float = 0
        
        logger.info(f"RockwoolScraper inicializálva: {self.config.base_url}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._init_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._close_browser()
    
    async def _init_browser(self):
        """Browser inicializálás"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.config.headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        self.context = await self.browser.new_context(
            user_agent=self.config.user_agent,
            locale='hu-HU'
        )
    
    async def _close_browser(self):
        """Browser bezárás"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
    def _rate_limit(self):
        """Rate limiting - késleltetés kérések között"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.config.request_delay:
            sleep_time = self.config.request_delay - time_since_last
            logger.debug(f"Rate limiting: várakozás {sleep_time:.2f} másodperc")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def _fetch_page(self, url: str, retries: int = None) -> Optional[BeautifulSoup]:
        """
        Biztonságos oldal letöltés retry logikával - Playwright alapú
        
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
                
                page = await self.context.new_page()
                await page.goto(url, timeout=self.config.timeout * 1000)
                
                # Várjuk meg, hogy a JavaScript betöltődjön
                await page.wait_for_load_state('networkidle')
                
                # HTML tartalom lekérése
                content = await page.content()
                await page.close()
                
                soup = BeautifulSoup(content, 'html.parser')
                logger.debug(f"Sikeres letöltés: {url}")
                return soup
                
            except Exception as e:
                logger.warning(f"Hiba az oldal letöltésénél {url}: {e}")
                if attempt < retries:
                    wait_time = (attempt + 1) * 2
                    logger.info(f"Újrapróbálkozás {wait_time} másodperc múlva...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Végleg sikertelen: {url}")
                    self.failed_urls.add(url)
                    return None
        
        return None
    
    async def discover_website_structure(self) -> Dict[str, List[str]]:
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
        main_page = await self._fetch_page(self.config.base_url)
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
    
    async def scrape_for_demo(self) -> List[Dict[str, str]]:
        """
        Egyszerűsített scraping DEMO célokra
        
        Returns:
            Lista termékekkel (name, url, full_text_content)
        """
        logger.info("DEMO scraping indítása...")
        
        products = []
        
        try:
            # Főoldal betöltése
            main_page = await self._fetch_page(self.config.base_url)
            if not main_page:
                logger.error("Nem sikerült betölteni a főoldalt")
                return products
            
            # Termék linkek keresése
            product_links = self._find_product_links(main_page)
            logger.info(f"Talált termék linkek: {len(product_links)}")
            
            # Első 10 termék feldolgozása (DEMO limitálás)
            for i, link in enumerate(product_links[:10]):
                logger.info(f"Termék scraping {i+1}/10: {link}")
                
                page_soup = await self._fetch_page(link)
                if page_soup:
                    # Teljes szöveges tartalom kinyerése
                    text_content = page_soup.get_text(separator=' ', strip=True)
                    
                    # Termék név kinyerése (title vagy h1)
                    name_elem = page_soup.find('h1') or page_soup.find('title')
                    name = name_elem.get_text(strip=True) if name_elem else f"Rockwool termék {i+1}"
                    
                    products.append({
                        'name': name,
                        'url': link,
                        'full_text_content': text_content[:10000]  # Első 10k karakter
                    })
                    
                await asyncio.sleep(1)  # Rövid várakozás
            
            logger.info(f"DEMO scraping befejezve: {len(products)} termék")
            return products
            
        except Exception as e:
            logger.error(f"Hiba a DEMO scraping során: {e}")
            return products
    
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
        
        # Minden linket megvizsgálunk
        links = soup.find_all('a', href=True)
        logger.info(f"Összes link száma a főoldalon: {len(links)}")
        
        # Debug: első 10 link kiírása
        for i, link in enumerate(links[:10]):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            logger.info(f"Link {i+1}: {href} - Text: {text}")
        
        # Termék oldalak jellemzői alapján azonosítás - bővített lista
        product_indicators = [
            'multirock', 'frontrock', 'deltarock', 'airrock', 
            'steprock', 'roofrock', 'hardrock', 'termekek',
            'products', 'product', 'solutions', 'megoldasok'
        ]
        
        for link in links:
            href = link.get('href', '').lower()
            text = link.get_text(strip=True).lower()
            
            # URL vagy szöveg alapján termék link azonosítás
            if (any(indicator in href for indicator in product_indicators) or
                any(indicator in text for indicator in product_indicators)):
                full_url = urljoin(self.config.base_url, link.get('href'))
                if self._is_rockwool_url(full_url):
                    product_links.append(full_url)
                    logger.info(f"Termék link találva: {full_url}")
        
        logger.info(f"Összes termék link: {len(product_links)}")
        return list(set(product_links))
    
    def _is_rockwool_url(self, url: str) -> bool:
        """Ellenőrzi, hogy az URL a Rockwool domain-hez tartozik-e"""
        parsed = urlparse(url)
        return 'rockwool.com' in parsed.netloc.lower()
    
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