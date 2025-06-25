"""
Category Mapper - Rockwool kategóriák normalizálása

Ez a modul kezeli a Rockwool weboldal különböző kategória elnevezéseinek
egységes kategóriákra való leképezését.
"""

import logging
from typing import Dict, Set

logger = logging.getLogger(__name__)


class CategoryMapper:
    """
    Rockwool kategóriák normalizálása és leképezése
    
    Funkcionalitás:
    - URL alapú kategória meghatározás
    - Terméknevek alapú kategorizálás  
    - Egységes kategória struktúra kialakítása
    """
    
    def __init__(self):
        # Fő kategóriák és aliasaik
        self.category_mappings = {
            'Tetőszigetelés': {
                'keywords': [
                    'teto', 'roof', 'tetoszigeteles', 'roofrock', 
                    'deltarock', 'pitched', 'lapos teto'
                ],
                'products': [
                    'roofrock', 'deltarock', 'rockplus'
                ]
            },
            'Homlokzati hőszigetelés': {
                'keywords': [
                    'homlokzat', 'facade', 'frontrock', 'frontis',
                    'hoszigeteles', 'thermal'
                ],
                'products': [
                    'frontrock', 'multirock'
                ]
            },
            'Padlószigetelés': {
                'keywords': [
                    'padlo', 'floor', 'steprock', 'impact',
                    'lepcsohang', 'zajcsokkentes'
                ],
                'products': [
                    'steprock', 'deltarock'
                ]
            },
            'Válaszfal szigetelés': {
                'keywords': [
                    'valaszfal', 'partition', 'belso', 'wall',
                    'airrock', 'osszefogas'
                ],
                'products': [
                    'airrock', 'multirock'
                ]
            },
            'Gépészeti szigetelés': {
                'keywords': [
                    'gepeszet', 'mechanical', 'csovezetek', 'pipe',
                    'wired mat', 'technical'
                ],
                'products': [
                    'wired mat', 'rockwool mat'
                ]
            },
            'Tűzvédelem': {
                'keywords': [
                    'tuzvedelem', 'fire', 'firesafe', 'hardrock',
                    'pozar', 'fire resistant'
                ],
                'products': [
                    'hardrock', 'firesafe'
                ]
            },
            'Hangszigetelés': {
                'keywords': [
                    'hangszigeteles', 'acoustic', 'sound', 'zaj',
                    'noise', 'rocksilence'
                ],
                'products': [
                    'rocksilence', 'acoustic'
                ]
            }
        }
        
        # Termék alapú kategória mapping
        self.product_category_map = {}
        for category, data in self.category_mappings.items():
            for product in data['products']:
                self.product_category_map[product.lower()] = category
    
    def map_category(self, raw_category: str, url: str = "", 
                    product_name: str = "") -> str:
        """
        Kategória normalizálása és leképezése
        
        Args:
            raw_category: Nyers kategória név
            url: Termék URL-je (opcionális)
            product_name: Termék neve (opcionális)
            
        Returns:
            Normalizált kategória név
        """
        # Elsődlegesen URL alapú kategorizálás
        if url:
            url_category = self._categorize_by_url(url)
            if url_category:
                return url_category
        
        # Terméknév alapú kategorizálás
        if product_name:
            product_category = self._categorize_by_product_name(product_name)
            if product_category:
                return product_category
        
        # Nyers kategória feldolgozása
        if raw_category:
            mapped_category = self._map_raw_category(raw_category)
            if mapped_category:
                return mapped_category
        
        # Alapértelmezett kategória
        logger.warning(f"Nem sikerült kategóriát meghatározni: "
                      f"raw='{raw_category}', url='{url}', "
                      f"product='{product_name}'")
        return "Általános szigetelés"
    
    def _categorize_by_url(self, url: str) -> str:
        """URL alapú kategorizálás"""
        url_lower = url.lower()
        
        for category, data in self.category_mappings.items():
            for keyword in data['keywords']:
                if keyword in url_lower:
                    logger.debug(f"URL alapú kategória: {category} ('{keyword}' in '{url}')")
                    return category
        
        return ""
    
    def _categorize_by_product_name(self, product_name: str) -> str:
        """Terméknév alapú kategorizálás"""
        product_lower = product_name.lower()
        
        # Direkt termék mapping
        for product_key, category in self.product_category_map.items():
            if product_key in product_lower:
                logger.debug(f"Terméknév alapú kategória: {category} ('{product_key}' in '{product_name}')")
                return category
        
        # Keyword alapú keresés a terméknevben
        for category, data in self.category_mappings.items():
            for keyword in data['keywords']:
                if keyword in product_lower:
                    logger.debug(f"Keyword alapú kategória: {category} ('{keyword}' in '{product_name}')")
                    return category
        
        return ""
    
    def _map_raw_category(self, raw_category: str) -> str:
        """Nyers kategória mapping"""
        raw_lower = raw_category.lower()
        
        # Direkt egyezések
        category_aliases = {
            'hőszigetelés': 'Homlokzati hőszigetelés',
            'hangszigetelés': 'Hangszigetelés', 
            'tetőszigetelés': 'Tetőszigetelés',
            'padlószigetelés': 'Padlószigetelés',
            'tűzvédelem': 'Tűzvédelem',
            'gépészeti': 'Gépészeti szigetelés',
            'thermal insulation': 'Homlokzati hőszigetelés',
            'acoustic insulation': 'Hangszigetelés',
            'roof insulation': 'Tetőszigetelés',
            'floor insulation': 'Padlószigetelés',
            'fire protection': 'Tűzvédelem'
        }
        
        for alias, category in category_aliases.items():
            if alias in raw_lower:
                return category
        
        # Keyword alapú keresés
        for category, data in self.category_mappings.items():
            for keyword in data['keywords']:
                if keyword in raw_lower:
                    return category
        
        return ""
    
    def get_all_categories(self) -> Set[str]:
        """Az összes elérhető kategória listája"""
        return set(self.category_mappings.keys())
    
    def get_category_keywords(self, category: str) -> Set[str]:
        """Egy kategória összes kulcsszava"""
        if category in self.category_mappings:
            data = self.category_mappings[category]
            return set(data['keywords'] + data['products'])
        return set()
    
    def validate_category(self, category: str) -> bool:
        """Ellenőrzi, hogy egy kategória érvényes-e"""
        return category in self.category_mappings or category == "Általános szigetelés" 