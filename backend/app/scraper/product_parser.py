"""
Product Parser - Rockwool termékoldal specifikus adatok kinyerése

Ez a modul kezeli a Rockwool weboldal termékoldalaira jellemző
HTML struktúrák elemzését és a releváns adatok kinyerését.
"""

import re
import logging
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class ProductParser:
    """
    Rockwool termékoldal parser osztály
    
    Funkcionalitás:
    - Termék névének és leírásának kinyerése
    - Műszaki specifikációk feldolgozása
    - Képek és dokumentumok URL-jeinek gyűjtése
    - Árak és elérhetőség információk (ha vannak)
    """
    
    def __init__(self):
        # Rockwool specifikus CSS szelektorok és szabályok
        self.name_selectors = [
            'h1',
            '.product-title',
            '.termek-nev',
            '.page-title',
            'title'
        ]
        
        self.description_selectors = [
            '.product-description',
            '.termek-leiras',
            '.felhasznalasi-terulet',
            '.application-area'
        ]
        
        self.specs_table_selectors = [
            '.technical-data table',
            '.muszaki-adatok table', 
            '.specifications table',
            'table'
        ]
    
    def parse_product_page(self, soup: BeautifulSoup, url: str) -> Dict:
        """
        Termékoldal fő adatainak kinyerése
        
        Args:
            soup: BeautifulSoup objektum a termékoldallal
            url: Termékoldal URL-je
            
        Returns:
            Dict a termék alapadataival
        """
        logger.debug(f"Termékoldal elemzése: {url}")
        
        # Termék név kinyerése
        name = self._extract_product_name(soup)
        
        # Leírás kinyerése
        description = self._extract_description(soup)
        
        # Kategória meghatározása URL és tartalom alapján
        category = self._extract_category(soup, url)
        
        # Ár és elérhetőség
        price = self._extract_price(soup)
        availability = self._extract_availability(soup)
        
        return {
            'name': name,
            'description': description,
            'category': category,
            'price': price,
            'availability': availability
        }
    
    def _extract_product_name(self, soup: BeautifulSoup) -> str:
        """Termék nevének kinyerése"""
        for selector in self.name_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 3:
                    # Rockwool specifikus tisztítás
                    text = re.sub(r'^ROCKWOOL\s*-?\s*', '', text, flags=re.IGNORECASE)
                    text = re.sub(r'\s*-\s*kőzetgyapot.*$', '', text, flags=re.IGNORECASE)
                    return text.strip()
        
        logger.warning("Nem sikerült terméknevét kinyerni")
        return "Ismeretlen termék"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Termék leírásának kinyerése"""
        descriptions = []
        
        for selector in self.description_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 20:
                    descriptions.append(text)
        
        # Ha nincs explicit leírás, első bekezdés használata
        if not descriptions:
            paragraphs = soup.find_all('p')
            for p in paragraphs[:3]:  # Első 3 bekezdés ellenőrzése
                text = p.get_text(strip=True)
                if len(text) > 50:
                    descriptions.append(text)
                    break
        
        return ' '.join(descriptions) if descriptions else ""
    
    def _extract_category(self, soup: BeautifulSoup, url: str) -> str:
        """Kategória meghatározása URL és tartalom alapján"""
        # URL alapú kategória meghatározás
        url_lower = url.lower()
        
        url_categories = {
            'tetoszigeteles': 'Tetőszigetelés',
            'homlokzat': 'Homlokzati hőszigetelés',
            'padlo': 'Padlószigetelés',
            'valaszfal': 'Válaszfal szigetelés',
            'gepeszet': 'Gépészeti szigetelés',
            'tuzvedelem': 'Tűzvédelem',
            'hangszigeteles': 'Hangszigetelés'
        }
        
        for keyword, category in url_categories.items():
            if keyword in url_lower:
                return category
        
        # Oldalon található kategória információ keresése
        breadcrumbs = soup.find_all(['nav', 'div'], class_=lambda x: x and 'breadcrumb' in x.lower())
        for breadcrumb in breadcrumbs:
            text = breadcrumb.get_text()
            for keyword, category in url_categories.items():
                if keyword in text.lower():
                    return category
        
        return "Általános szigetelés"
    
    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Ár információ kinyerése (ha elérhető)"""
        price_selectors = [
            '.price',
            '.ar',
            '.cost',
            '[class*="price"]'
        ]
        
        for selector in price_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                # Árak kinyerése számokkal
                price_match = re.search(r'(\d+(?:[.,]\d+)*)', text.replace(' ', ''))
                if price_match:
                    try:
                        price_str = price_match.group(1).replace(',', '.')
                        return float(price_str)
                    except ValueError:
                        continue
        
        return None
    
    def _extract_availability(self, soup: BeautifulSoup) -> bool:
        """Elérhetőség információ kinyerése"""
        # Rockwool alapvetően minden terméke elérhető a weboldalon
        availability_indicators = [
            'készleten',
            'available',
            'elérhető',
            'rendelhető'
        ]
        
        page_text = soup.get_text().lower()
        for indicator in availability_indicators:
            if indicator in page_text:
                return True
        
        # Alapértelmezetten elérhető
        return True
    
    def extract_technical_specifications(self, soup: BeautifulSoup) -> Dict:
        """
        Műszaki specifikációk kinyerése táblázatokból
        
        Args:
            soup: BeautifulSoup objektum
            
        Returns:
            Dict a műszaki adatokkal
        """
        specs = {}
        
        # Táblázatok keresése
        for selector in self.specs_table_selectors:
            tables = soup.select(selector)
            for table in tables:
                table_specs = self._parse_specs_table(table)
                specs.update(table_specs)
        
        # Strukturált adatok keresése definíciós listákban
        dl_elements = soup.find_all('dl')
        for dl in dl_elements:
            dl_specs = self._parse_definition_list(dl)
            specs.update(dl_specs)
        
        return specs
    
    def _parse_specs_table(self, table: BeautifulSoup) -> Dict:
        """Műszaki adatok táblázat feldolgozása"""
        specs = {}
        
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                
                if key and value and not key.lower() in ['paraméter', 'érték', 'parameter', 'value']:
                    # Egységek kezelése
                    specs[key] = self._normalize_spec_value(value)
        
        return specs
    
    def _parse_definition_list(self, dl: BeautifulSoup) -> Dict:
        """Definíciós lista feldolgozása"""
        specs = {}
        
        terms = dl.find_all('dt')
        definitions = dl.find_all('dd')
        
        for i, term in enumerate(terms):
            if i < len(definitions):
                key = term.get_text(strip=True)
                value = definitions[i].get_text(strip=True)
                
                if key and value:
                    specs[key] = self._normalize_spec_value(value)
        
        return specs
    
    def _normalize_spec_value(self, value: str) -> str:
        """Műszaki érték normalizálása"""
        # Felesleges szóközök eltávolítása
        value = re.sub(r'\s+', ' ', value).strip()
        
        # Különleges karakterek kezelése
        value = value.replace('∙', '·')
        value = value.replace('−', '-')
        
        return value
    
    def extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Termékhez tartozó képek URL-jeinek gyűjtése
        
        Args:
            soup: BeautifulSoup objektum
            base_url: Weboldal alap URL-je
            
        Returns:
            Lista a kép URL-ekkel
        """
        images = []
        
        # Képek keresése különböző helyekről
        img_selectors = [
            'img[src*="product"]',
            'img[src*="termek"]',
            '.product-image img',
            '.termek-kep img',
            '.gallery img',
            'img[alt*="ROCKWOOL"]'
        ]
        
        for selector in img_selectors:
            img_elements = soup.select(selector)
            for img in img_elements:
                src = img.get('src') or img.get('data-src')
                if src:
                    full_url = urljoin(base_url, src)
                    if self._is_product_image(src):
                        images.append(full_url)
        
        return list(set(images))  # Duplikátumok eltávolítása
    
    def extract_documents(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Termékhez tartozó dokumentumok URL-jeinek gyűjtése
        
        Args:
            soup: BeautifulSoup objektum  
            base_url: Weboldal alap URL-je
            
        Returns:
            Lista a dokumentum URL-ekkel
        """
        documents = []
        
        # Dokumentum linkek keresése
        doc_selectors = [
            'a[href$=".pdf"]',
            'a[href*="termekadatlap"]',
            'a[href*="datasheet"]',
            'a[href*="letoltes"]',
            'a[href*="download"]'
        ]
        
        for selector in doc_selectors:
            doc_elements = soup.select(selector)
            for doc in doc_elements:
                href = doc.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    documents.append(full_url)
        
        return list(set(documents))
    
    def _is_product_image(self, src: str) -> bool:
        """Ellenőrzi, hogy a kép valóban termékképe-e"""
        # Kizárt képtípusok
        excluded_keywords = [
            'logo', 'icon', 'banner', 'header', 'footer',
            'nav', 'menu', 'button', 'arrow', 'social'
        ]
        
        src_lower = src.lower()
        return not any(keyword in src_lower for keyword in excluded_keywords) 