"""
Scraping Celery Tasks - Automatizált adatgyűjtési feladatok

Ez a modul tartalmazza a Rockwool és egyéb gyártók
automatizált adatgyűjtésére szolgáló Celery feladatokat.
"""

import logging
from typing import Dict, List
from datetime import datetime, timedelta

from celery import shared_task
from celery.exceptions import Retry, MaxRetriesExceededError

from ..scraper import RockwoolScraper, ScrapingConfig, DatabaseIntegration, DataValidator
from ..database import get_db

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def test_scraper_connection(self):
    """
    Scraper kapcsolat tesztelése
    
    Returns:
        Dict: Kapcsolat teszt eredménye
    """
    try:
        import requests
        
        # Rockwool weboldal elérhetőség teszt
        response = requests.get('https://www.rockwool.hu', timeout=10)
        
        return {
            'success': True,
            'status_code': response.status_code,
            'timestamp': datetime.now().isoformat(),
            'message': 'Rockwool weboldal elérhető'
        }
        
    except Exception as e:
        logger.error(f"Scraper kapcsolat teszt sikertelen: {e}")
        
        # Retry logika
        if self.request.retries < self.max_retries:
            logger.info(f"Újrapróbálkozás {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(countdown=60)
        
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'message': 'Rockwool weboldal nem elérhető'
        }


@shared_task(bind=True, max_retries=2, default_retry_delay=1800)
def scheduled_rockwool_scraping(self, max_products_per_category: int = 20):
    """
    Ütemezett Rockwool scraping - napi futtatásra
    
    Args:
        max_products_per_category: Maximum termékek kategóriánként
        
    Returns:
        Dict: Scraping eredmény statisztikákkal
    """
    start_time = datetime.now()
    logger.info("Ütemezett Rockwool scraping indítása")
    
    try:
        # Scraper konfiguráció (konzervatív beállítások)
        config = ScrapingConfig(
            request_delay=3.0,
            max_requests_per_minute=20,
            max_retries=3,
            timeout=45
        )
        
        # Scraper inicializálás
        scraper = RockwoolScraper(config)
        validator = DataValidator()
        
        # Weboldal struktúra feltérképezése
        logger.info("Weboldal struktúra feltérképezése...")
        structure = scraper.discover_website_structure()
        
        if not structure['categories']:
            raise Exception("Nem sikerült kategóriákat találni")
        
        # Termékek scraping-je kategóriánként
        all_products = []
        categories_processed = 0
        
        for category_url in structure['categories']:
            try:
                logger.info(f"Kategória feldolgozása: {category_url}")
                
                category_products = scraper._scrape_category_products(category_url)
                
                # Limitálás
                if len(category_products) > max_products_per_category:
                    category_products = category_products[:max_products_per_category]
                
                all_products.extend(category_products)
                categories_processed += 1
                
                logger.info(f"Kategória kész: {len(category_products)} termék")
                
            except Exception as cat_error:
                logger.error(f"Kategória hiba {category_url}: {cat_error}")
                continue
        
        # Validálás
        logger.info("Termékek validálása...")
        validation_report = validator.get_validation_report(all_products)
        
        # Adatbázisba mentés
        logger.info("Adatbázisba mentés...")
        db_session = next(get_db())
        try:
            db_integration = DatabaseIntegration(db_session)
            db_stats = db_integration.save_scraped_products_bulk(all_products)
        finally:
            db_session.close()
        
        # Eredmény összefoglalás
        duration = (datetime.now() - start_time).total_seconds()
        
        result = {
            'success': True,
            'started_at': start_time.isoformat(),
            'completed_at': datetime.now().isoformat(),
            'duration_seconds': duration,
            'categories_processed': categories_processed,
            'total_products': len(all_products),
            'validation_stats': validation_report['summary'],
            'database_stats': db_stats,
            'scraper_stats': scraper.get_scraping_statistics()
        }
        
        logger.info(f"Ütemezett scraping befejezve: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Ütemezett scraping hiba: {e}")
        
        # Retry logika
        if self.request.retries < self.max_retries:
            retry_delay = 1800 * (self.request.retries + 1)  # 30, 60 perc
            logger.info(f"Scraping újrapróbálkozás {retry_delay} másodperc múlva")
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


@shared_task(bind=True, max_retries=1, default_retry_delay=3600)
def weekly_full_scraping(self):
    """
    Heti teljes Rockwool scraping - minden termék
    
    Returns:
        Dict: Teljes scraping eredmény
    """
    start_time = datetime.now()
    logger.info("Heti teljes Rockwool scraping indítása")
    
    try:
        # Lassabb, de alaposabb konfiguráció
        config = ScrapingConfig(
            request_delay=4.0,
            max_requests_per_minute=15,
            max_retries=5,
            timeout=60
        )
        
        scraper = RockwoolScraper(config)
        validator = DataValidator()
        
        # Teljes scraping (korlátok nélkül)
        logger.info("Teljes termékadatok scraping...")
        all_products = scraper.scrape_all_products()
        
        # Validálás
        validation_report = validator.get_validation_report(all_products)
        
        # Adatbázisba mentés
        db_session = next(get_db())
        try:
            db_integration = DatabaseIntegration(db_session)
            db_stats = db_integration.save_scraped_products_bulk(all_products)
        finally:
            db_session.close()
        
        # Eredmény
        duration = (datetime.now() - start_time).total_seconds()
        
        result = {
            'success': True,
            'type': 'weekly_full_scraping',
            'started_at': start_time.isoformat(),
            'completed_at': datetime.now().isoformat(),
            'duration_hours': duration / 3600,
            'total_products': len(all_products),
            'validation_stats': validation_report['summary'],
            'database_stats': db_stats,
            'scraper_stats': scraper.get_scraping_statistics()
        }
        
        logger.info(f"Heti teljes scraping befejezve: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Heti teljes scraping hiba: {e}")
        
        if self.request.retries < self.max_retries:
            logger.info("Heti scraping újrapróbálkozás 1 óra múlva")
            raise self.retry(countdown=3600)
        
        duration = (datetime.now() - start_time).total_seconds()
        return {
            'success': False,
            'type': 'weekly_full_scraping',
            'error': str(e),
            'started_at': start_time.isoformat(),
            'failed_at': datetime.now().isoformat(),
            'duration_hours': duration / 3600,
            'retry_count': self.request.retries
        }


@shared_task(bind=True)
def scrape_specific_urls(self, urls: List[str], save_to_database: bool = True):
    """
    Specifikus URL-ek scraping-je
    
    Args:
        urls: Scraping-elni kívánt URL-ek listája
        save_to_database: Mentés adatbázisba
        
    Returns:
        Dict: Scraping eredmény
    """
    start_time = datetime.now()
    logger.info(f"Specifikus URL-ek scraping: {len(urls)} URL")
    
    try:
        config = ScrapingConfig(
            request_delay=2.0,
            max_requests_per_minute=30
        )
        
        scraper = RockwoolScraper(config)
        validator = DataValidator()
        
        # URL-ek feldolgozása
        scraped_products = []
        failed_urls = []
        
        for url in urls:
            try:
                product = scraper._scrape_single_product(url)
                if product and validator.validate_product(product):
                    scraped_products.append(product)
                else:
                    failed_urls.append(url)
                    
            except Exception as url_error:
                logger.error(f"URL scraping hiba {url}: {url_error}")
                failed_urls.append(url)
        
        # Adatbázisba mentés
        db_stats = None
        if save_to_database and scraped_products:
            db_session = next(get_db())
            try:
                db_integration = DatabaseIntegration(db_session)
                db_stats = db_integration.save_scraped_products_bulk(scraped_products)
            finally:
                db_session.close()
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            'success': True,
            'started_at': start_time.isoformat(),
            'completed_at': datetime.now().isoformat(),
            'duration_seconds': duration,
            'requested_urls': len(urls),
            'successful_products': len(scraped_products),
            'failed_urls': len(failed_urls),
            'failed_url_list': failed_urls,
            'database_stats': db_stats
        }
        
    except Exception as e:
        logger.error(f"Specifikus URL scraping hiba: {e}")
        
        duration = (datetime.now() - start_time).total_seconds()
        return {
            'success': False,
            'error': str(e),
            'started_at': start_time.isoformat(),
            'failed_at': datetime.now().isoformat(),
            'duration_seconds': duration,
            'requested_urls': len(urls) if urls else 0
        }


@shared_task
def get_scraping_queue_status():
    """
    Scraping feladatok queue státuszának lekérése
    
    Returns:
        Dict: Queue státusz információk
    """
    try:
        from ..celery_app import celery_app
        
        # Aktív feladatok
        active_tasks = celery_app.control.inspect().active()
        
        # Queue hosszak
        queue_lengths = celery_app.control.inspect().reserved()
        
        # Registered tasks
        registered_tasks = celery_app.control.inspect().registered()
        
        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'active_tasks': active_tasks,
            'queue_lengths': queue_lengths,
            'registered_tasks': registered_tasks
        }
        
    except Exception as e:
        logger.error(f"Queue státusz lekérés hiba: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        } 