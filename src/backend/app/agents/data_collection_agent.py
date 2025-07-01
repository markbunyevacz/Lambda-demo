"""
Data Collection Agent - Adatgyűjtő Agent

Ez az agent koordinálja a különböző adatforrásokból történő adatgyűjtést,
validálást és tárolást a Lambda demo számára.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

from ..models.product import Product
from ..scraper.data_validator import DataValidator
from ..database import get_db
from ..scrapers.rockwool_final.brochure_and_pricelist_scraper import RockwoolBrochureScraper as RockwoolApiScraper
from .brightdata_agent import BrightDataMCPAgent

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Adatforrás típusok"""
    API_PDF = "api_pdf"
    WEB_SCRAPING = "web_scraping"
    BRIGHTDATA_MCP = "brightdata_mcp"
    MANUAL_IMPORT = "manual_import"
    CSV_IMPORT = "csv_import"


class CollectionStatus(Enum):
    """Gyűjtési állapotok"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class DataCollectionAgent:
    """
    Adatgyűjtő Agent osztály
    
    Funkcionalitás:
    - Különböző adatforrások koordinálása
    - Adatvalidálás és tisztítás
    - Hibakezelés és retry logika
    - Perzisztens adattárolás
    - Gyűjtési metrikák és monitoring
    """
    
    def __init__(self, batch_size: int = 50, max_retries: int = 3):
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.validator = DataValidator()
        
        # Agent állapot
        self.agent_id = f"data_collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.status = CollectionStatus.PENDING
        
        # Data sources inicializálása
        self.api_scraper = RockwoolApiScraper()
        self.mcp_agent = BrightDataMCPAgent()
        
        # Gyűjtési statisztikák
        self.collection_stats = {
            'total_items_collected': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'storage_successes': 0,
            'storage_failures': 0,
            'sources_used': [],
            'collection_duration': 0,
            'last_collection': None
        }
        
        # Hibakezelési konfiguráció
        self.retry_delays = [1, 3, 5]  # seconds
        self.timeout_seconds = 300  # 5 perc
    
    async def collect_data(self, sources: List[DataSource], 
                          targets: Optional[Union[List[str], str, int]] = None,
                          validate: bool = True,
                          store: bool = True) -> Dict:
        """
        Főbb adatgyűjtési funkció
        
        Args:
            sources: Használandó adatforrások listája
            targets: Specifikus célpontok (URL-ek, keresési kifejezések, limit)
            validate: Adatok validálása
            store: Adatok mentése adatbázisba
            
        Returns:
            Gyűjtési eredmény és statisztikák
        """
        start_time = datetime.now()
        self.status = CollectionStatus.IN_PROGRESS
        
        logger.info(f"Adatgyűjtés indítása - Agent ID: {self.agent_id}")
        logger.info(f"Adatforrások: {[s.value for s in sources]}")
        
        collected_data = []
        collection_results = {}
        
        try:
            # Párhuzamos gyűjtés különböző forrásokból
            tasks = []
            for source in sources:
                task = asyncio.create_task(
                    self._collect_from_source(source, targets),
                    name=f"collect_{source.value}"
                )
                tasks.append(task)
            
            # Eredmények összegyűjtése
            source_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(source_results):
                source = sources[i]
                if isinstance(result, Exception):
                    logger.error(f"Adatgyűjtés hiba {source.value}: {result}")
                    collection_results[source.value] = {'success': False, 'error': str(result)}
                else:
                    collection_results[source.value] = {'success': True, 'data_count': len(result)}
                    collected_data.extend(result)
                    self.collection_stats['sources_used'].append(source.value)
            
            # Adatok normalizálása és validálása
            if validate:
                collected_data = await self._validate_collected_data(collected_data)
            
            # Adatok mentése
            if store and collected_data:
                await self._store_collected_data(collected_data)
            
            # Statisztikák frissítése
            self.collection_stats['total_items_collected'] += len(collected_data)
            self.collection_stats['collection_duration'] = (datetime.now() - start_time).total_seconds()
            self.collection_stats['last_collection'] = datetime.now().isoformat()
            
            self.status = CollectionStatus.COMPLETED if collected_data else CollectionStatus.PARTIAL
            
            result = {
                'agent_id': self.agent_id,
                'status': self.status.value,
                'data_collected': len(collected_data),
                'sources_used': list(set(self.collection_stats['sources_used'])),
                'collection_results': collection_results,
                'statistics': self.collection_stats.copy(),
                'data': collected_data if not store else None,  # Ne adjuk vissza a nagy adatokat ha el vannak mentve
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Adatgyűjtés befejezve: {len(collected_data)} elem összegyűjtve")
            return result
            
        except Exception as e:
            self.status = CollectionStatus.FAILED
            logger.error(f"Adatgyűjtés kritikus hiba: {e}")
            return {
                'agent_id': self.agent_id,
                'status': self.status.value,
                'error': str(e),
                'data_collected': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _collect_from_source(self, source: DataSource, targets: Any) -> List[Dict]:
        """Adatgyűjtés egy adott forrásból"""
        logger.info(f"Adatgyűjtés indítása: {source.value}")
        
        try:
            if source == DataSource.API_PDF:
                return await self._collect_from_api_pdf(targets)
            elif source == DataSource.BRIGHTDATA_MCP:
                return await self._collect_from_brightdata_mcp(targets)
            elif source == DataSource.WEB_SCRAPING:
                return await self._collect_from_web_scraping(targets)
            elif source == DataSource.MANUAL_IMPORT:
                return await self._collect_from_manual_import(targets)
            elif source == DataSource.CSV_IMPORT:
                return await self._collect_from_csv_import(targets)
            else:
                logger.warning(f"Ismeretlen adatforrás: {source}")
                return []
                
        except Exception as e:
            logger.error(f"Adatgyűjtési hiba {source.value}: {e}")
            return []
    
    async def _collect_from_api_pdf(self, targets: Any) -> List[Dict]:
        """API PDF adatgyűjtés"""
        try:
            if isinstance(targets, int):
                products = await self.api_scraper.scrape_all_product_datasheets(limit=targets)
            else:
                products = await self.api_scraper.scrape_all_product_datasheets()
            
            # Normalizálás
            normalized_products = []
            for product in products:
                normalized = {
                    'name': product.get('name', 'Ismeretlen termék'),
                    'description': product.get('full_text_content', '')[:500],
                    'category': 'Termékadatlap (PDF)',
                    'source_url': product.get('url'),
                    'scraped_at': datetime.now().isoformat(),
                    'data_source': DataSource.API_PDF.value,
                    'technical_specs': {},
                    'applications': [],
                    'raw_data': product.get('full_text_content', '')
                }
                normalized_products.append(normalized)
            
            logger.info(f"API PDF gyűjtés: {len(normalized_products)} termék")
            return normalized_products
            
        except Exception as e:
            logger.error(f"API PDF gyűjtési hiba: {e}")
            return []
    
    async def _collect_from_brightdata_mcp(self, targets: Any) -> List[Dict]:
        """BrightData MCP adatgyűjtés"""
        try:
            if isinstance(targets, list):
                # URL lista
                products = await self.mcp_agent.scrape_rockwool_with_ai(targets)
            elif isinstance(targets, str):
                # Keresési kifejezés
                search_results = await self.mcp_agent.search_rockwool_products(targets)
                urls = [result['url'] for result in search_results[:5]]  # Limitálás
                products = await self.mcp_agent.scrape_rockwool_with_ai(urls)
            else:
                # Alapértelmezett Rockwool scraping
                default_urls = [
                    "https://www.rockwool.hu/termekek/",
                    "https://www.rockwool.hu"
                ]
                products = await self.mcp_agent.scrape_rockwool_with_ai(default_urls)
            
            # Data source jelölés hozzáadása
            for product in products:
                product['data_source'] = DataSource.BRIGHTDATA_MCP.value
            
            logger.info(f"BrightData MCP gyűjtés: {len(products)} termék")
            return products
            
        except Exception as e:
            logger.error(f"BrightData MCP gyűjtési hiba: {e}")
            return []
    
    async def _collect_from_web_scraping(self, targets: Any) -> List[Dict]:
        """Hagyományos web scraping (placeholder)"""
        logger.info("Hagyományos web scraping - Nincs implementálva")
        return []
    
    async def _collect_from_manual_import(self, targets: Any) -> List[Dict]:
        """Manuális adatimport (placeholder)"""
        logger.info("Manuális adatimport - Nincs implementálva")
        return []
    
    async def _collect_from_csv_import(self, targets: Any) -> List[Dict]:
        """CSV adatimport (placeholder)"""
        logger.info("CSV adatimport - Nincs implementálva")
        return []
    
    async def _validate_collected_data(self, data: List[Dict]) -> List[Dict]:
        """Összegyűjtött adatok validálása"""
        logger.info(f"Adatok validálása: {len(data)} elem")
        
        validated_data = []
        
        for item in data:
            try:
                if self.validator.validate_product(item):
                    validated_data.append(item)
                    self.collection_stats['successful_validations'] += 1
                else:
                    logger.warning(f"Validációs hiba: {item.get('name', 'Névtelen')}")
                    self.collection_stats['failed_validations'] += 1
            except Exception as e:
                logger.error(f"Validációs kivétel: {e}")
                self.collection_stats['failed_validations'] += 1
        
        logger.info(f"Validálás befejezve: {len(validated_data)}/{len(data)} sikeres")
        return validated_data
    
    async def _store_collected_data(self, data: List[Dict]) -> None:
        """Adatok mentése adatbázisba"""
        logger.info(f"Adatok mentése: {len(data)} elem")
        
        try:
            db = get_db()
            
            for item in data:
                try:
                    # Product objektum létrehozása
                    product = Product(
                        name=item.get('name'),
                        description=item.get('description'),
                        category=item.get('category'),
                        source_url=item.get('source_url'),
                        technical_specs=item.get('technical_specs', {}),
                        applications=item.get('applications', []),
                        scraped_at=datetime.fromisoformat(item.get('scraped_at', datetime.now().isoformat())),
                        data_source=item.get('data_source')
                    )
                    
                    db.add(product)
                    self.collection_stats['storage_successes'] += 1
                    
                except Exception as e:
                    logger.error(f"Termék mentési hiba: {e}")
                    self.collection_stats['storage_failures'] += 1
            
            db.commit()
            logger.info(f"Adatmentés befejezve: {self.collection_stats['storage_successes']} sikeres")
            
        except Exception as e:
            logger.error(f"Adatbázis mentési hiba: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def get_collection_statistics(self) -> Dict:
        """Gyűjtési statisztikák lekérése"""
        return {
            'agent_id': self.agent_id,
            'status': self.status.value,
            'statistics': self.collection_stats.copy(),
            'timestamp': datetime.now().isoformat()
        }
    
    async def health_check(self) -> Dict:
        """Agent egészség ellenőrzés"""
        health_status = {
            'agent_id': self.agent_id,
            'status': self.status.value,
            'healthy': True,
            'errors': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # API scraper teszt
            if not hasattr(self.api_scraper, 'scrape_all_product_datasheets'):
                health_status['errors'].append('API scraper nem elérhető')
                health_status['healthy'] = False
            
            # MCP agent teszt
            if not self.mcp_agent.mcp_available:
                health_status['errors'].append('BrightData MCP agent nem elérhető')
                # Nem critical hiba
            
            # Validator teszt
            if not hasattr(self.validator, 'validate_product'):
                health_status['errors'].append('Data validator nem elérhető')
                health_status['healthy'] = False
            
        except Exception as e:
            health_status['healthy'] = False
            health_status['errors'].append(f'Health check hiba: {str(e)}')
        
        return health_status 