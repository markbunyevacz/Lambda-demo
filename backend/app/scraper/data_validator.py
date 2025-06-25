"""
Data Validator - Scraped adatok validálása

Ez a modul validálja a Rockwool scraper által összegyűjtött
termékadatokat, biztosítva az adatok minőségét és konzisztenciáját.
"""

import logging
import re
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Scraped termékadatok validálása
    
    Funkcionalitás:
    - Kötelező mezők ellenőrzése
    - Adatformátum validálás
    - Termékadatok konzisztencia vizsgálat
    - Hiányzó vagy hibás adatok jelzése
    """
    
    def __init__(self):
        # Kötelező mezők a termékekhez
        self.required_fields = [
            'name', 'url', 'category'
        ]
        
        # Opcionális, de ajánlott mezők
        self.recommended_fields = [
            'description', 'technical_specs', 'images'
        ]
        
        # Minimum karakterszám különböző mezőkhöz
        self.min_lengths = {
            'name': 3,
            'description': 10,
            'category': 3
        }
        
        # Érvényes kategóriák (CategoryMapper-rel szinkronban)
        self.valid_categories = {
            'Tetőszigetelés',
            'Homlokzati hőszigetelés', 
            'Padlószigetelés',
            'Válaszfal szigetelés',
            'Gépészeti szigetelés',
            'Tűzvédelem',
            'Hangszigetelés',
            'Általános szigetelés'
        }
    
    def validate_product(self, product) -> bool:
        """
        Teljes termék validálás
        
        Args:
            product: ScrapedProduct objektum
            
        Returns:
            True ha a termék érvényes, False egyébként
        """
        try:
            # Alapvető mezők ellenőrzése
            if not self._validate_required_fields(product):
                return False
            
            # Név validálás
            if not self._validate_name(product.name):
                return False
            
            # URL validálás
            if not self._validate_url(product.url):
                return False
            
            # Kategória validálás
            if not self._validate_category(product.category):
                return False
            
            # Leírás validálás (ha van)
            if product.description and not self._validate_description(product.description):
                logger.warning(f"Gyenge leírás: {product.name}")
            
            # Műszaki adatok validálás
            if not self._validate_technical_specs(product.technical_specs):
                logger.warning(f"Hiányos műszaki adatok: {product.name}")
            
            # Képek validálás
            if not self._validate_images(product.images):
                logger.warning(f"Hiányzó képek: {product.name}")
            
            # Dátum validálás
            if not self._validate_scraped_date(product.scraped_at):
                return False
            
            logger.debug(f"Termék validálás sikeres: {product.name}")
            return True
            
        except Exception as e:
            logger.error(f"Hiba a validálás során {product.name}: {e}")
            return False
    
    def _validate_required_fields(self, product) -> bool:
        """Kötelező mezők ellenőrzése"""
        for field in self.required_fields:
            if not hasattr(product, field):
                logger.error(f"Hiányzó kötelező mező: {field}")
                return False
            
            value = getattr(product, field)
            if not value or (isinstance(value, str) and not value.strip()):
                logger.error(f"Üres kötelező mező: {field}")
                return False
        
        return True
    
    def _validate_name(self, name: str) -> bool:
        """Terméknév validálás"""
        if not isinstance(name, str):
            logger.error("Terméknév nem string")
            return False
        
        name = name.strip()
        
        # Minimum hossz
        if len(name) < self.min_lengths['name']:
            logger.error(f"Túl rövid terméknév: '{name}'")
            return False
        
        # Maximum hossz
        if len(name) > 200:
            logger.error(f"Túl hosszú terméknév: '{name[:50]}...'")
            return False
        
        # Gyanús tartalmak kizárása
        suspicious_patterns = [
            r'^(error|404|not found)',
            r'^(lorem ipsum)',
            r'^(\s*$)',
            r'^(test|példa|sample)'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                logger.error(f"Gyanús terméknév: '{name}'")
                return False
        
        return True
    
    def _validate_url(self, url: str) -> bool:
        """URL validálás"""
        if not isinstance(url, str):
            logger.error("URL nem string")
            return False
        
        # Alap URL formátum ellenőrzés
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, url):
            logger.error(f"Hibás URL formátum: {url}")
            return False
        
        # Rockwool domain ellenőrzés
        if 'rockwool.hu' not in url.lower():
            logger.warning(f"Nem Rockwool URL: {url}")
        
        return True
    
    def _validate_category(self, category: str) -> bool:
        """Kategória validálás"""
        if not isinstance(category, str):
            logger.error("Kategória nem string")
            return False
        
        if category not in self.valid_categories:
            logger.error(f"Érvénytelen kategória: '{category}'")
            return False
        
        return True
    
    def _validate_description(self, description: str) -> bool:
        """Leírás validálás"""
        if not isinstance(description, str):
            return False
        
        description = description.strip()
        
        # Minimum hossz
        if len(description) < self.min_lengths['description']:
            return False
        
        # Maximum hossz
        if len(description) > 5000:
            return False
        
        # Gyanús tartalmak
        if re.search(r'^(lorem ipsum|test|példa)', description, re.IGNORECASE):
            return False
        
        return True
    
    def _validate_technical_specs(self, technical_specs: Dict) -> bool:
        """Műszaki specifikációk validálás"""
        if not isinstance(technical_specs, dict):
            return False
        
        # Nem szükséges, hogy legyen, de ha van, akkor ellenőrizzük
        if not technical_specs:
            return True
        
        # Validálás, hogy vannak-e értékes adatok
        valid_specs = 0
        for key, value in technical_specs.items():
            if isinstance(key, str) and isinstance(value, str):
                if len(key.strip()) > 2 and len(value.strip()) > 1:
                    valid_specs += 1
        
        return valid_specs > 0
    
    def _validate_images(self, images: List[str]) -> bool:
        """Képek validálás"""
        if not isinstance(images, list):
            return False
        
        # Nem kötelező, de ajánlott
        if not images:
            return True
        
        # URL formátum ellenőrzés a képeknél
        valid_images = 0
        for image_url in images:
            if isinstance(image_url, str) and re.match(r'^https?://', image_url):
                valid_images += 1
        
        return valid_images == len(images)
    
    def _validate_scraped_date(self, scraped_at) -> bool:
        """Scraping dátum validálás"""
        if scraped_at is None:
            return True  # Opcionális mező
        
        if not isinstance(scraped_at, datetime):
            logger.error("scraped_at nem datetime objektum")
            return False
        
        # Nem lehet jövőbeli dátum
        if scraped_at > datetime.now():
            logger.error("scraped_at jövőbeli dátum")
            return False
        
        return True
    
    def validate_bulk_data(self, products: List) -> Dict[str, int]:
        """
        Termékek tömeges validálása
        
        Args:
            products: ScrapedProduct objektumok listája
            
        Returns:
            Dict a validálási statisztikákkal
        """
        stats = {
            'total': len(products),
            'valid': 0,
            'invalid': 0,
            'warnings': 0
        }
        
        for product in products:
            if self.validate_product(product):
                stats['valid'] += 1
            else:
                stats['invalid'] += 1
        
        stats['success_rate'] = (stats['valid'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        logger.info(f"Tömeges validálás: {stats['valid']}/{stats['total']} "
                   f"sikeres ({stats['success_rate']:.1f}%)")
        
        return stats
    
    def get_validation_report(self, products: List) -> Dict:
        """
        Részletes validálási jelentés
        
        Args:
            products: ScrapedProduct objektumok listája
            
        Returns:
            Dict a részletes jelentéssel
        """
        report = {
            'summary': self.validate_bulk_data(products),
            'issues': {
                'missing_descriptions': 0,
                'missing_technical_specs': 0,
                'missing_images': 0,
                'invalid_categories': []
            }
        }
        
        for product in products:
            # Hiányzó leírások
            if not product.description or len(product.description.strip()) < 10:
                report['issues']['missing_descriptions'] += 1
            
            # Hiányzó műszaki adatok
            if not product.technical_specs or len(product.technical_specs) == 0:
                report['issues']['missing_technical_specs'] += 1
            
            # Hiányzó képek
            if not product.images or len(product.images) == 0:
                report['issues']['missing_images'] += 1
            
            # Érvénytelen kategóriák
            if product.category not in self.valid_categories:
                report['issues']['invalid_categories'].append({
                    'product': product.name,
                    'category': product.category
                })
        
        return report 