"""
BrightData MCP Celery Tasks - AI-vezérelt scraping feladatok

Ez a modul tartalmazza a BrightData MCP agenteket használó
automatizált adatgyűjtési feladatokat.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from celery import shared_task
from celery.exceptions import Retry, MaxRetriesExceededError

from ..agents import BrightDataMCPAgent, ScrapingCoordinator
from ..agents.scraping_coordinator import ScrapingStrategy
from ..database import get_db
from ..scraper.database_integration import DatabaseIntegration

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def test_brightdata_mcp_connection(self):
    """
    BrightData MCP kapcsolat tesztelése
    
    Returns:
        Dict: Kapcsolat teszt eredménye
    """
    try:
        import asyncio
        
        # BrightData MCP Agent tesztelése
        async def test_connection():
            agent = BrightDataMCPAgent()
            return await agent.test_mcp_connection()
        
        # Asyncio futtatás
        result = asyncio.run(test_connection())
        
        return {
            'success': result.get('success', False),
            'message': result.get('message', 'BrightData MCP teszt befejezve'),
            'timestamp': datetime.now().isoformat(),
            'details': result
        }
        
    except Exception as e:
        logger.error(f"BrightData MCP teszt sikertelen: {e}")
        
        # Retry logika
        if self.request.retries < self.max_retries:
            logger.info(f"BrightData teszt újrapróbálkozás {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(countdown=60)
        
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'message': 'BrightData MCP kapcsolat sikertelen'
        }


@shared_task(bind=True, max_retries=2, default_retry_delay=600)
def ai_powered_rockwool_scraping(self, target_urls: List[str] = None, 
                                max_products: int = 10, 
                                save_to_database: bool = True):
    """
    AI-vezérelt Rockwool scraping BrightData MCP-vel
    
    Args:
        target_urls: Konkrét URL-ek listája (opcionális)
        max_products: Maximum termékek száma
        save_to_database: Adatbázisba mentés
        
    Returns:
        Dict: Scraping eredmény
    """
    start_time = datetime.now()
    logger.info("AI-vezérelt Rockwool scraping indítása")
    
    try:
        import asyncio
        
        async def run_ai_scraping():
            agent = BrightDataMCPAgent()
            
            if target_urls:
                # Konkrét URL-ek scraping-je
                products = await agent.scrape_rockwool_with_ai(target_urls[:max_products])
            else:
                # Általános keresés és scraping
                search_results = await agent.search_rockwool_products("Rockwool szigetelőanyag")
                
                # URL-ek kinyerése és limitálása
                urls_to_scrape = [result['url'] for result in search_results[:max_products]]
                
                if urls_to_scrape:
                    products = await agent.scrape_rockwool_with_ai(urls_to_scrape)
                else:
                    # Fallback: alapértelmezett URL-ek
                    default_urls = [
                        "https://www.rockwool.hu/termekek/",
                        "https://www.rockwool.hu"
                    ]
                    products = await agent.scrape_rockwool_with_ai(default_urls[:max_products])
            
            return products, agent.get_scraping_statistics()
        
        # AI scraping végrehajtása
        products, ai_stats = asyncio.run(run_ai_scraping())
        
        # Adatbázisba mentés
        db_stats = None
        if save_to_database and products:
            db_session = next(get_db())
            try:
                db_integration = DatabaseIntegration(db_session)
                db_stats = db_integration.save_scraped_products_bulk(products)
            finally:
                db_session.close()
        
        # Eredmény összefoglalás
        duration = (datetime.now() - start_time).total_seconds()
        
        result = {
            'success': True,
            'started_at': start_time.isoformat(),
            'completed_at': datetime.now().isoformat(),
            'duration_seconds': duration,
            'scraped_products': len(products),
            'ai_scraping_stats': ai_stats,
            'database_stats': db_stats,
            'sample_products': products[:3] if products else []  # Első 3 termék minta
        }
        
        logger.info(f"AI scraping befejezve: {len(products)} termék")
        return result
        
    except Exception as e:
        logger.error(f"AI scraping hiba: {e}")
        
        # Retry logika
        if self.request.retries < self.max_retries:
            retry_delay = 600 * (self.request.retries + 1)  # 10, 20 perc
            logger.info(f"AI scraping újrapróbálkozás {retry_delay} másodperc múlva")
            raise self.retry(countdown=retry_delay)
        
        # Végső hiba
        duration = (datetime.now() - start_time).total_seconds()
        return {
            'success': False,
            'error': str(e),
            'started_at': start_time.isoformat(),
            'failed_at': datetime.now().isoformat(),
            'duration_seconds': duration,
            'retry_count': self.request.retries
        }


@shared_task(bind=True, max_retries=1, default_retry_delay=1200)
def coordinated_scraping_with_fallback(self, 
                                     strategy: str = "api_fallback_mcp",
                                     max_products: int = 20,
                                     target_input = None):
    """
    Koordinált scraping több stratégiával és fallback logikával
    
    Args:
        strategy: Scraping stratégia (api_only, mcp_only, api_fallback_mcp, stb.)
        max_products: Maximum termékek száma
        target_input: URL lista, keresési kifejezés vagy limit
        
    Returns:
        Dict: Koordinált scraping eredmény
    """
    start_time = datetime.now()
    logger.info(f"Koordinált scraping indítása - Stratégia: {strategy}")
    
    try:
        import asyncio
        
        async def run_coordinated_scraping():
            # Stratégia enum konvertálás
            strategy_map = {
                'api_only': ScrapingStrategy.API_ONLY,
                'mcp_only': ScrapingStrategy.MCP_ONLY,
                'api_fallback_mcp': ScrapingStrategy.API_FALLBACK_MCP,
                'mcp_fallback_api': ScrapingStrategy.MCP_FALLBACK_API,
                'parallel': ScrapingStrategy.PARALLEL
            }
            
            selected_strategy = strategy_map.get(strategy, ScrapingStrategy.API_FALLBACK_MCP)
            
            # Coordinator inicializálás
            coordinator = ScrapingCoordinator(strategy=selected_strategy)
            
            # Input feldolgozás
            scraping_input = target_input
            if isinstance(target_input, int) and target_input != max_products:
                scraping_input = min(target_input, max_products)
            elif not target_input:
                scraping_input = max_products
            
            # Koordinált scraping
            products = await coordinator.scrape_products(scraping_input)
            
            # Limitálás
            if len(products) > max_products:
                products = products[:max_products]
            
            return products, coordinator.get_coordination_statistics()
        
        # Scraping végrehajtása
        products, coordination_stats = asyncio.run(run_coordinated_scraping())
        
        # Adatbázisba mentés
        db_session = next(get_db())
        try:
            db_integration = DatabaseIntegration(db_session)
            db_stats = db_integration.save_scraped_products_bulk(products)
        finally:
            db_session.close()
        
        # Eredmény
        duration = (datetime.now() - start_time).total_seconds()
        
        result = {
            'success': True,
            'strategy_used': strategy,
            'started_at': start_time.isoformat(),
            'completed_at': datetime.now().isoformat(),
            'duration_seconds': duration,
            'total_products': len(products),
            'coordination_stats': coordination_stats,
            'database_stats': db_stats,
            'sample_products': products[:2] if products else []
        }
        
        logger.info(f"Koordinált scraping befejezve: {len(products)} termék, stratégia: {strategy}")
        return result
        
    except Exception as e:
        logger.error(f"Koordinált scraping hiba: {e}")
        
        if self.request.retries < self.max_retries:
            logger.info("Koordinált scraping újrapróbálkozás 20 perc múlva")
            raise self.retry(countdown=1200)
        
        duration = (datetime.now() - start_time).total_seconds()
        return {
            'success': False,
            'strategy_used': strategy,
            'error': str(e),
            'started_at': start_time.isoformat(),
            'failed_at': datetime.now().isoformat(),
            'duration_seconds': duration,
            'retry_count': self.request.retries
        }


@shared_task
def test_all_scraping_methods():
    """
    Összes scraping módszer tesztelése és teljesítmény összehasonlítás
    
    Returns:
        Dict: Teszt eredmények
    """
    start_time = datetime.now()
    logger.info("Összes scraping módszer tesztelése")
    
    try:
        import asyncio
        
        async def run_comprehensive_test():
            coordinator = ScrapingCoordinator()
            
            # Scraper tesztelés
            test_results = await coordinator.test_all_scrapers()
            
            return test_results
        
        # Teszt végrehajtása
        test_results = asyncio.run(run_comprehensive_test())
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            'success': True,
            'test_started_at': start_time.isoformat(),
            'test_completed_at': datetime.now().isoformat(),
            'test_duration_seconds': duration,
            'scraper_availability': test_results,
            'recommended_strategy': test_results.get('coordination', {}).get('recommended_strategy'),
            'summary': {
                'api_available': test_results.get('api_scraper', {}).get('available', False),
                'mcp_available': test_results.get('mcp_agent', {}).get('available', False),
                'both_available': (
                    test_results.get('api_scraper', {}).get('available', False) and
                    test_results.get('mcp_agent', {}).get('available', False)
                )
            }
        }
        
    except Exception as e:
        logger.error(f"Scraping módszer teszt hiba: {e}")
        
        duration = (datetime.now() - start_time).total_seconds()
        return {
            'success': False,
            'error': str(e),
            'test_started_at': start_time.isoformat(),
            'test_failed_at': datetime.now().isoformat(),
            'test_duration_seconds': duration
        }


@shared_task(bind=True, max_retries=2)
def brightdata_search_and_scrape(self, search_query: str, max_results: int = 5):
    """
    BrightData keresés és azonnali scraping
    
    Args:
        search_query: Keresési kifejezés
        max_results: Maximum eredmények száma
        
    Returns:
        Dict: Keresés és scraping eredmény
    """
    start_time = datetime.now()
    logger.info(f"BrightData keresés és scraping: {search_query}")
    
    try:
        import asyncio
        
        async def search_and_scrape():
            agent = BrightDataMCPAgent()
            
            # Keresés
            search_results = await agent.search_rockwool_products(search_query)
            
            if not search_results:
                return [], [], {}
            
            # URL-ek limitálása
            urls_to_scrape = [result['url'] for result in search_results[:max_results]]
            
            # Scraping
            scraped_products = await agent.scrape_rockwool_with_ai(urls_to_scrape)
            
            # Statisztikák
            stats = agent.get_scraping_statistics()
            
            return search_results, scraped_products, stats
        
        # Keresés és scraping végrehajtása
        search_results, scraped_products, ai_stats = asyncio.run(search_and_scrape())
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            'success': True,
            'search_query': search_query,
            'started_at': start_time.isoformat(),
            'completed_at': datetime.now().isoformat(),
            'duration_seconds': duration,
            'search_results_count': len(search_results),
            'scraped_products_count': len(scraped_products),
            'search_results': search_results,
            'scraped_products': scraped_products,
            'ai_stats': ai_stats
        }
        
    except Exception as e:
        logger.error(f"BrightData keresés és scraping hiba: {e}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"Keresés újrapróbálkozás")
            raise self.retry(countdown=300)
        
        duration = (datetime.now() - start_time).total_seconds()
        return {
            'success': False,
            'search_query': search_query,
            'error': str(e),
            'started_at': start_time.isoformat(),
            'failed_at': datetime.now().isoformat(),
            'duration_seconds': duration,
            'retry_count': self.request.retries
        } 