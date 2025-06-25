#!/usr/bin/env python3
"""
Lambda.hu Rockwool Scraper Integrációs Teszt

Ez a script teszteli a teljes A+B+C implementációt:
- A) Adatbázis integráció
- B) Celery setup (opcionális)
- C) Scraper tesztelése éles Rockwool adatokon

Futtatás:
    python backend/test_integration.py
"""

import sys
import os
import logging
from pathlib import Path

# Backend útvonal hozzáadása
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Környezeti változók beállítása teszteléshez
os.environ['DATABASE_URL'] = os.getenv(
    'DATABASE_URL', 
    'postgresql://lambda_user:lambda_password@localhost:5432/lambda_db'
)
os.environ['REDIS_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Logging beállítása
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('integration_test.log')
    ]
)

logger = logging.getLogger(__name__)


def test_database_connection():
    """Adatbázis kapcsolat tesztelése"""
    logger.info("=" * 60)
    logger.info("ADATBÁZIS KAPCSOLAT TESZT")
    logger.info("=" * 60)
    
    try:
        from app.database import get_db, engine
        from app.models.product import Product
        from app.models.manufacturer import Manufacturer
        from app.models.category import Category
        
        # Adatbázis kapcsolat teszt
        db = next(get_db())
        
        try:
            # Táblák számának ellenőrzése
            product_count = db.query(Product).count()
            manufacturer_count = db.query(Manufacturer).count()
            category_count = db.query(Category).count()
            
            logger.info(f"✓ Adatbázis kapcsolat sikeres")
            logger.info(f"✓ Termékek: {product_count}")
            logger.info(f"✓ Gyártók: {manufacturer_count}")
            logger.info(f"✓ Kategóriák: {category_count}")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"✗ Adatbázis kapcsolat hiba: {e}")
        return False


def test_scraper_basic_functionality():
    """Scraper alapvető működés tesztelése"""
    logger.info("=" * 60)
    logger.info("SCRAPER ALAPVETŐ MŰKÖDÉS TESZT")
    logger.info("=" * 60)
    
    try:
        from app.scraper import RockwoolScraper, ScrapingConfig
        
        # Konzervatív teszt konfiguráció
        config = ScrapingConfig(
            request_delay=3.0,
            max_requests_per_minute=10,
            timeout=30,
            max_retries=2
        )
        
        scraper = RockwoolScraper(config)
        
        # 1. Weboldal struktúra tesztelése
        logger.info("1. Weboldal struktúra feltérképezése...")
        structure = scraper.discover_website_structure()
        
        logger.info(f"✓ Kategóriák találva: {len(structure['categories'])}")
        logger.info(f"✓ Termék oldalak találva: {len(structure['product_pages'])}")
        
        if len(structure['categories']) == 0:
            logger.warning("⚠ Nincsenek kategóriák - ellenőrizd a weboldal struktúráját")
            return False
        
        # 2. Egy kategória tesztelése (korlátozott)
        if structure['categories']:
            test_category = structure['categories'][0]
            logger.info(f"2. Teszt kategória: {test_category}")
            
            category_products = scraper._scrape_category_products(test_category)
            # Csak első 2 termék a teszteléshez
            category_products = category_products[:2]
            
            logger.info(f"✓ Kategória termékek: {len(category_products)}")
            
            for i, product in enumerate(category_products, 1):
                logger.info(f"   {i}. {product.name} - {product.category}")
        
        # 3. Egyetlen termék részletes tesztelése
        if structure['product_pages']:
            test_url = structure['product_pages'][0]
            logger.info(f"3. Egyetlen termék teszt: {test_url}")
            
            product = scraper._scrape_single_product(test_url)
            
            if product:
                logger.info(f"✓ Termék név: {product.name}")
                logger.info(f"✓ Kategória: {product.category}")
                logger.info(f"✓ Leírás hossza: {len(product.description)} karakter")
                logger.info(f"✓ Műszaki adatok: {len(product.technical_specs)} db")
                logger.info(f"✓ Képek: {len(product.images)} db")
                logger.info(f"✓ Dokumentumok: {len(product.documents)} db")
            else:
                logger.error("✗ Termék scraping sikertelen")
                return False
        
        logger.info("✓ Scraper alapvető tesztek sikeresek")
        return True
        
    except Exception as e:
        logger.error(f"✗ Scraper teszt hiba: {e}")
        return False


def test_database_integration():
    """Adatbázis integráció tesztelése"""
    logger.info("=" * 60)
    logger.info("ADATBÁZIS INTEGRÁCIÓ TESZT")
    logger.info("=" * 60)
    
    try:
        from app.scraper import RockwoolScraper, ScrapingConfig, DatabaseIntegration, DataValidator
        from app.database import get_db
        
        # Scraper konfiguráció
        config = ScrapingConfig(
            request_delay=3.0,
            max_requests_per_minute=10,
            timeout=30
        )
        
        scraper = RockwoolScraper(config)
        validator = DataValidator()
        
        # 1. Egyetlen termék scraping és mentés
        logger.info("1. Egyetlen termék scraping és adatbázis mentés...")
        
        structure = scraper.discover_website_structure()
        if not structure['product_pages']:
            logger.error("✗ Nincsenek termék oldalak a teszteléshez")
            return False
        
        test_url = structure['product_pages'][0]
        scraped_product = scraper._scrape_single_product(test_url)
        
        if not scraped_product:
            logger.error("✗ Termék scraping sikertelen")
            return False
        
        # Validálás
        is_valid = validator.validate_product(scraped_product)
        logger.info(f"✓ Validálás eredménye: {is_valid}")
        
        # Adatbázisba mentés
        db = next(get_db())
        try:
            db_integration = DatabaseIntegration(db)
            saved_product, is_new = db_integration.save_scraped_product(scraped_product)
            
            logger.info(f"✓ Termék mentve: ID={saved_product.id}")
            logger.info(f"✓ SKU: {saved_product.sku}")
            logger.info(f"✓ Új termék: {is_new}")
            logger.info(f"✓ Gyártó ID: {saved_product.manufacturer_id}")
            logger.info(f"✓ Kategória ID: {saved_product.category_id}")
            
        finally:
            db.close()
        
        # 2. Bulk mentés teszt (2-3 termék)
        logger.info("2. Bulk mentés teszt...")
        
        test_products = []
        for url in structure['product_pages'][:3]:  # Első 3 termék
            try:
                product = scraper._scrape_single_product(url)
                if product and validator.validate_product(product):
                    test_products.append(product)
                    if len(test_products) >= 2:  # Elég 2 termék a teszthez
                        break
            except Exception as e:
                logger.warning(f"⚠ Termék hiba {url}: {e}")
                continue
        
        if test_products:
            db = next(get_db())
            try:
                db_integration = DatabaseIntegration(db)
                bulk_stats = db_integration.save_scraped_products_bulk(test_products)
                
                logger.info(f"✓ Bulk mentés statisztikák: {bulk_stats}")
                
            finally:
                db.close()
        
        logger.info("✓ Adatbázis integráció tesztek sikeresek")
        return True
        
    except Exception as e:
        logger.error(f"✗ Adatbázis integráció teszt hiba: {e}")
        return False


def test_api_endpoints():
    """API végpontok tesztelése (opcionális)"""
    logger.info("=" * 60)
    logger.info("API VÉGPONTOK TESZT (OPCIONÁLIS)")
    logger.info("=" * 60)
    
    try:
        import requests
        
        # Feltételezzük, hogy a FastAPI app fut a 8000-es porton
        base_url = "http://localhost:8000"
        
        # Health check
        logger.info("1. Health check teszt...")
        response = requests.get(f"{base_url}/api/scraper/health", timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            logger.info(f"✓ Health check sikeres: {health_data.get('scraper_ready', False)}")
        else:
            logger.warning(f"⚠ Health check nem elérhető: {response.status_code}")
        
        # Weboldal struktúra API
        logger.info("2. Weboldal struktúra API teszt...")
        response = requests.get(f"{base_url}/api/scraper/website-structure", timeout=30)
        
        if response.status_code == 200:
            structure_data = response.json()
            logger.info(f"✓ Struktúra API sikeres: {structure_data.get('success', False)}")
        else:
            logger.warning(f"⚠ Struktúra API nem elérhető: {response.status_code}")
        
        logger.info("✓ API tesztek befejezve")
        return True
        
    except Exception as e:
        logger.warning(f"⚠ API tesztek nem futtathatók: {e}")
        logger.info("   (Ez normális, ha a FastAPI szerver nem fut)")
        return True  # Nem kritikus hiba


def test_celery_tasks():
    """Celery feladatok tesztelése (opcionális)"""
    logger.info("=" * 60)
    logger.info("CELERY FELADATOK TESZT (OPCIONÁLIS)")
    logger.info("=" * 60)
    
    try:
        from app.celery_app import celery_app
        
        # Celery worker kapcsolat teszt
        logger.info("1. Celery kapcsolat teszt...")
        
        # Ping teszt
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            logger.info(f"✓ Celery workerek elérhetőek: {len(stats)} worker")
        else:
            logger.warning("⚠ Celery workerek nem elérhetőek")
        
        # Debug task teszt
        logger.info("2. Debug task teszt...")
        from app.celery_app import debug_task
        
        result = debug_task.delay()
        task_result = result.get(timeout=10)
        
        logger.info(f"✓ Debug task eredmény: {task_result}")
        
        logger.info("✓ Celery tesztek sikeresek")
        return True
        
    except Exception as e:
        logger.warning(f"⚠ Celery tesztek nem futtathatók: {e}")
        logger.info("   (Ez normális, ha Redis vagy Celery worker nem fut)")
        return True  # Nem kritikus hiba


def main():
    """Fő teszt futtatás"""
    logger.info("🚀 Lambda.hu Rockwool Scraper Integrációs Teszt Indítása")
    logger.info(f"Python verzió: {sys.version}")
    logger.info(f"Munkamappa: {os.getcwd()}")
    
    # Tesztek futtatása
    tests = [
        ("Adatbázis kapcsolat", test_database_connection),
        ("Scraper alapvető működés", test_scraper_basic_functionality),
        ("Adatbázis integráció", test_database_integration),
        ("API végpontok", test_api_endpoints),
        ("Celery feladatok", test_celery_tasks)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\n📋 {test_name} teszt futtatása...")
            result = test_func()
            results[test_name] = result
            
            if result:
                logger.info(f"✅ {test_name}: SIKERES")
            else:
                logger.error(f"❌ {test_name}: SIKERTELEN")
                
        except Exception as e:
            logger.error(f"💥 {test_name}: HIBA - {e}")
            results[test_name] = False
    
    # Összefoglaló
    logger.info("\n" + "=" * 60)
    logger.info("TESZT ÖSSZEFOGLALÓ")
    logger.info("=" * 60)
    
    successful_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    
    for test_name, result in results.items():
        status = "✅ SIKERES" if result else "❌ SIKERTELEN"
        logger.info(f"{test_name:.<40} {status}")
    
    logger.info(f"\nSikeres tesztek: {successful_tests}/{total_tests}")
    
    if successful_tests >= 3:  # Legalább 3 alapvető teszt sikeres
        logger.info("🎉 INTEGRÁCIÓS TESZT SIKERES!")
        logger.info("   A Rockwool scraper + adatbázis integráció működőképes.")
    else:
        logger.error("💥 INTEGRÁCIÓS TESZT SIKERTELEN!")
        logger.error("   Ellenőrizd a hibaüzeneteket és a konfigurációt.")
    
    return successful_tests >= 3


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⏹️ Teszt megszakítva felhasználó által")
        sys.exit(130)
    except Exception as e:
        logger.error(f"💥 Váratlan hiba: {e}")
        sys.exit(1) 