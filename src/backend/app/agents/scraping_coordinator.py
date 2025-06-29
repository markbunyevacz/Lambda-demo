"""
Scraping Coordinator - Scraping stratégiák koordinálása

Ez a modul koordinálja a különböző scraping módszereket:
- Hagyományos API scraping (RockwoolApiScraper)  
- BrightData MCP AI scraping (BrightDataMCPAgent)
- Hibakezelés és fallback logika
"""

import logging
from typing import Dict, List, Optional, Union
from datetime import datetime
from enum import Enum

from app.database import SessionLocal
from app.models import Product, ScrapedData
from app.scraper.data_validator import DataValidator
from app.scrapers.rockwool import RockwoolScraper
from .brightdata_agent import BrightDataMCPAgent

logger = logging.getLogger(__name__)


class ScrapingStrategy(Enum):
    """Scraping stratégiák"""
    API_ONLY = "api_only"
    MCP_ONLY = "mcp_only"
    API_FALLBACK_MCP = "api_fallback_mcp"
    MCP_FALLBACK_API = "mcp_fallback_api"
    PARALLEL = "parallel"


class ScrapingCoordinator:
    """
    Scraping Coordinator osztály
    
    Funkcionalitás:
    - Több scraping módszer koordinálása
    - Fallback logika implementation
    - Eredmények összehasonlítása és validálása
    - Teljesítmény optimalizálás
    """
    
    def __init__(self):
        """
        Scraping Coordinator inicializálása
        """
        # Session inicializálása
        self.db_session = SessionLocal()
        
        # Scraper inicializálás
        self.api_scraper = RockwoolScraper()
        self.mcp_agent = BrightDataMCPAgent()
        
        # Koordináció statisztikák
        self.coordination_stats = {
            'total_requests': 0,
            'api_successful': 0,
            'mcp_successful': 0,
            'fallback_used': 0,
            'validation_failures': 0,
            'strategy_usage': {}
        }
    
    async def scrape_products(self, target_input: Union[List[str], str, int] = None) -> List[Dict]:
        """
        Főbb scraping funkció - stratégia alapján
        
        Args:
            target_input: URL lista, keresési kifejezés, vagy termék limit
            
        Returns:
            Lista a scraped termék adatokkal
        """
        start_time = datetime.now()
        self.coordination_stats['total_requests'] += 1
        
        logger.info(f"Scraping koordinálás indítása - Stratégia: {self.strategy.value}")
        
        try:
            if self.strategy == ScrapingStrategy.API_ONLY:
                return await self._scrape_api_only(target_input)
            elif self.strategy == ScrapingStrategy.MCP_ONLY:
                return await self._scrape_mcp_only(target_input)
            elif self.strategy == ScrapingStrategy.API_FALLBACK_MCP:
                return await self._scrape_api_fallback_mcp(target_input)
            elif self.strategy == ScrapingStrategy.MCP_FALLBACK_API:
                return await self._scrape_mcp_fallback_api(target_input)
            elif self.strategy == ScrapingStrategy.PARALLEL:
                return await self._scrape_parallel(target_input)
            else:
                logger.error(f"Ismeretlen scraping stratégia: {self.strategy}")
                return []
                
        except Exception as e:
            logger.error(f"Scraping koordinálás hiba: {e}")
            return []
        finally:
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Scraping koordinálás befejezve - Időtartam: {duration:.2f}s")
    
    async def _scrape_api_only(self, target_input) -> List[Dict]:
        """Csak API scraping használata"""
        logger.info("API-only scraping végrehajtása")
        
        try:
            if isinstance(target_input, int):
                # Limit alapú scraping
                products = await self.api_scraper.scrape_all_product_datasheets(limit=target_input)
            else:
                # Teljes scraping
                products = await self.api_scraper.scrape_all_product_datasheets()
            
            # Adatok normalizálása
            normalized_products = []
            for product in products:
                normalized = self._normalize_api_product(product)
                if self.validator.validate_product(normalized):
                    normalized_products.append(normalized)
                    self.coordination_stats['api_successful'] += 1
                else:
                    self.coordination_stats['validation_failures'] += 1
            
            return normalized_products
            
        except Exception as e:
            logger.error(f"API scraping hiba: {e}")
            return []
    
    async def _scrape_mcp_only(self, target_input) -> List[Dict]:
        """Csak MCP scraping használata"""
        logger.info("MCP-only scraping végrehajtása")
        
        try:
            # Ha URL lista van megadva
            if isinstance(target_input, list):
                products = await self.mcp_agent.scrape_rockwool_with_ai(target_input)
            elif isinstance(target_input, str):
                # Keresés alapú scraping
                search_results = await self.mcp_agent.search_rockwool_products(target_input)
                urls = [result['url'] for result in search_results]
                products = await self.mcp_agent.scrape_rockwool_with_ai(urls)
            else:
                # Általános Rockwool scraping
                rockwool_urls = [
                    "https://www.rockwool.hu/termekek/",
                    "https://www.rockwool.hu"
                ]
                products = await self.mcp_agent.scrape_rockwool_with_ai(rockwool_urls)
            
            self.coordination_stats['mcp_successful'] += len(products)
            return products
            
        except Exception as e:
            logger.error(f"MCP scraping hiba: {e}")
            return []
    
    async def _scrape_api_fallback_mcp(self, target_input) -> List[Dict]:
        """API scraping elsődlegesen, MCP fallback"""
        logger.info("API-first stratégia végrehajtása")
        
        # Először API próbálkozás
        products = await self._scrape_api_only(target_input)
        
        # Ha sikeres és elegendő adat van
        if products and len(products) >= 5:
            logger.info(f"API scraping sikeres: {len(products)} termék")
            return products
        
        # Fallback MCP-re
        logger.info("API scraping elégtelen - Fallback MCP-re")
        self.coordination_stats['fallback_used'] += 1
        
        mcp_products = await self._scrape_mcp_only(target_input)
        
        # Eredmények kombinálása
        combined_products = products + mcp_products
        unique_products = self._remove_duplicates(combined_products)
        
        return unique_products
    
    async def _scrape_mcp_fallback_api(self, target_input) -> List[Dict]:
        """MCP scraping elsődlegesen, API fallback"""
        logger.info("MCP-first stratégia végrehajtása")
        
        # Először MCP próbálkozás
        products = await self._scrape_mcp_only(target_input)
        
        # Ha sikeres és elegendő adat van
        if products and len(products) >= 3:
            logger.info(f"MCP scraping sikeres: {len(products)} termék")
            return products
        
        # Fallback API-ra
        logger.info("MCP scraping elégtelen - Fallback API-ra")
        self.coordination_stats['fallback_used'] += 1
        
        api_products = await self._scrape_api_only(target_input)
        
        # Eredmények kombinálása
        combined_products = products + api_products
        unique_products = self._remove_duplicates(combined_products)
        
        return unique_products
    
    async def _scrape_parallel(self, target_input) -> List[Dict]:
        """Párhuzamos scraping mindkét módszerrel"""
        logger.info("Párhuzamos scraping végrehajtása")
        
        import asyncio
        
        try:
            # Párhuzamos scraping
            api_task = asyncio.create_task(self._scrape_api_only(target_input))
            mcp_task = asyncio.create_task(self._scrape_mcp_only(target_input))
            
            # Eredmények várása
            api_products, mcp_products = await asyncio.gather(
                api_task, mcp_task, return_exceptions=True
            )
            
            # Exception handling
            if isinstance(api_products, Exception):
                logger.error(f"API scraping hiba párhuzamos módban: {api_products}")
                api_products = []
            
            if isinstance(mcp_products, Exception):
                logger.error(f"MCP scraping hiba párhuzamos módban: {mcp_products}")
                mcp_products = []
            
            # Eredmények kombinálása
            all_products = (api_products or []) + (mcp_products or [])
            unique_products = self._remove_duplicates(all_products)
            
            logger.info(f"Párhuzamos scraping eredmény: {len(unique_products)} egyedi termék")
            return unique_products
            
        except Exception as e:
            logger.error(f"Párhuzamos scraping hiba: {e}")
            return []
    
    def _normalize_api_product(self, api_product: Dict) -> Dict:
        """API termék normalizálása közös formátumra"""
        return {
            'name': api_product.get('name', 'Ismeretlen termék'),
            'description': api_product.get('full_text_content', '')[:500],  # Limitálás
            'category': 'Termékadatlap (PDF)',
            'source_url': api_product.get('url'),
            'scraped_at': datetime.now().isoformat(),
            'scraper_type': 'api_pdf',
            'technical_specs': {},
            'applications': [],
            'raw_data': api_product.get('full_text_content', '')
        }
    
    def _remove_duplicates(self, products: List[Dict]) -> List[Dict]:
        """Duplikátumok eltávolítása"""
        seen = set()
        unique_products = []
        
        for product in products:
            # Azonosító készítése
            identifier = (
                product.get('source_url', ''),
                product.get('name', '').lower().strip()
            )
            
            if identifier not in seen and identifier != ('', ''):
                seen.add(identifier)
                unique_products.append(product)
        
        logger.info(f"Duplikátum szűrés: {len(products)} -> {len(unique_products)} termék")
        return unique_products
    
    def get_coordination_statistics(self) -> Dict:
        """Koordináció statisztikák lekérése"""
        total_successful = (
            self.coordination_stats['api_successful'] + 
            self.coordination_stats['mcp_successful']
        )
        
        return {
            **self.coordination_stats,
            'total_successful': total_successful,
            'success_rate': (
                total_successful / max(self.coordination_stats['total_requests'], 1)
            ) * 100,
            'current_strategy': self.strategy.value,
            'timestamp': datetime.now().isoformat()
        }
    
    async def test_all_scrapers(self) -> Dict:
        """Összes scraper tesztelése"""
        logger.info("Scraper tesztelés indítása")
        
        results = {
            'api_scraper': {'available': False, 'error': None},
            'mcp_agent': {'available': False, 'error': None},
            'coordination': {'recommended_strategy': None}
        }
        
        # API scraper teszt
        try:
            test_products = await self.api_scraper.scrape_all_product_datasheets(limit=1)
            results['api_scraper']['available'] = len(test_products) > 0
            if not results['api_scraper']['available']:
                results['api_scraper']['error'] = "Nincs termék eredmény"
        except Exception as e:
            results['api_scraper']['error'] = str(e)
        
        # MCP agent teszt
        try:
            mcp_test = await self.mcp_agent.test_mcp_connection()
            results['mcp_agent']['available'] = mcp_test.get('success', False)
            if not results['mcp_agent']['available']:
                results['mcp_agent']['error'] = mcp_test.get('error', 'Ismeretlen hiba')
        except Exception as e:
            results['mcp_agent']['error'] = str(e)
        
        # Stratégia ajánlás
        if results['api_scraper']['available'] and results['mcp_agent']['available']:
            results['coordination']['recommended_strategy'] = ScrapingStrategy.PARALLEL.value
        elif results['api_scraper']['available']:
            results['coordination']['recommended_strategy'] = ScrapingStrategy.API_ONLY.value
        elif results['mcp_agent']['available']:
            results['coordination']['recommended_strategy'] = ScrapingStrategy.MCP_ONLY.value
        else:
            results['coordination']['recommended_strategy'] = "NONE_AVAILABLE"
        
        logger.info(f"Scraper teszt befejezve: {results['coordination']['recommended_strategy']}")
        return results 