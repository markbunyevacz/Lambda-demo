"""
Rockwool Scraper Teszt Script

Ez a script bemutatja és teszteli a Rockwool scraper funkcionalitását.
Használható a scraper működésének ellenőrzésére és hibakeresésre.
"""

import asyncio
import logging
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Scraper modulok importálása
from .rockwool_scraper import RockwoolScraper, ScrapingConfig
from .data_validator import DataValidator

# Logging beállítása
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scraper_test.log')
    ]
)

logger = logging.getLogger(__name__)


class ScraperTester:
    """
    Rockwool Scraper tesztelő osztály
    
    Funkcionalitás:
    - Alapvető scraper funkciók tesztelése
    - Weboldal struktúra elemzése
    - Minta termékek scraping-je
    - Eredmények validálása és mentése
    """
    
    def __init__(self):
        # Teszt konfiguráció (lassabb, biztonságosabb)
        self.config = ScrapingConfig(
            max_requests_per_minute=10,
            request_delay=3.0,
            timeout=30,
            max_retries=2
        )
        
        self.scraper = RockwoolScraper(self.config)
        self.validator = DataValidator()
        
        # Eredmények mentési helye
        self.results_dir = Path('./scraper_results')
        self.results_dir.mkdir(exist_ok=True)
    
    def test_website_discovery(self):
        """Weboldal struktúra feltérképezésének tesztje"""
        logger.info("=== WEBOLDAL STRUKTÚRA FELTÉRKÉPEZÉSE ===")
        
        try:
            structure = self.scraper.discover_website_structure()
            
            logger.info(f"Talált kategóriák: {len(structure['categories'])}")
            for i, category_url in enumerate(structure['categories'][:5], 1):
                logger.info(f"  {i}. {category_url}")
            
            logger.info(f"Talált termék oldalak: {len(structure['product_pages'])}")
            for i, product_url in enumerate(structure['product_pages'][:5], 1):
                logger.info(f"  {i}. {product_url}")
            
            # Struktúra mentése
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            structure_file = self.results_dir / f"website_structure_{timestamp}.json"
            
            with open(structure_file, 'w', encoding='utf-8') as f:
                json.dump(structure, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Weboldal struktúra mentve: {structure_file}")
            return structure
            
        except Exception as e:
            logger.error(f"Hiba a weboldal feltérképezésében: {e}")
            return None
    
    def test_single_product_scraping(self, product_url: str = None):
        """Egyetlen termék scraping tesztje"""
        logger.info("=== EGYETLEN TERMÉK SCRAPING TESZT ===")
        
        # Alapértelmezett teszt URL (ha nem adunk meg)
        if not product_url:
            product_url = "https://www.rockwool.hu/termekek-es-megoldasok/rockwool-termekek/homlokzati-hoszigeteles/frontrock-max-e/"
        
        try:
            logger.info(f"Termék scraping: {product_url}")
            product = self.scraper._scrape_single_product(product_url)
            
            if product:
                logger.info(f"Sikeres scraping:")
                logger.info(f"  Név: {product.name}")
                logger.info(f"  Kategória: {product.category}")
                logger.info(f"  Leírás hossza: {len(product.description)} karakter")
                logger.info(f"  Műszaki adatok: {len(product.technical_specs)} db")
                logger.info(f"  Képek: {len(product.images)} db")
                logger.info(f"  Dokumentumok: {len(product.documents)} db")
                
                # Validálás
                is_valid = self.validator.validate_product(product)
                logger.info(f"  Validálás: {'✓ SIKERES' if is_valid else '✗ SIKERTELEN'}")
                
                # Mentés
                self._save_product_sample(product)
                return product
            else:
                logger.error("Termék scraping sikertelen")
                return None
                
        except Exception as e:
            logger.error(f"Hiba a termék scraping során: {e}")
            return None
    
    def test_category_scraping(self, max_products: int = 3):
        """Kategória szintű scraping teszt"""
        logger.info("=== KATEGÓRIA SCRAPING TESZT ===")
        
        try:
            # Weboldal struktúra lekérése
            structure = self.scraper.discover_website_structure()
            
            if not structure['categories']:
                logger.warning("Nincsenek kategóriák a scraping-hez")
                return []
            
            # Első kategória tesztelése
            test_category = structure['categories'][0]
            logger.info(f"Teszt kategória: {test_category}")
            
            # Kategória termékek scraping-je (limitált)
            products = self.scraper._scrape_category_products(test_category)
            
            # Limitálás a teszteléshez
            products = products[:max_products]
            
            logger.info(f"Kategóriából scraped termékek: {len(products)}")
            
            # Validálás
            validation_stats = self.validator.validate_bulk_data(products)
            logger.info(f"Validálási eredmények: {validation_stats}")
            
            # Eredmények mentése
            self._save_category_results(products, test_category)
            
            return products
            
        except Exception as e:
            logger.error(f"Hiba a kategória scraping során: {e}")
            return []
    
    def test_full_scraping(self, max_products_per_category: int = 2):
        """Teljes scraping teszt (korlátozott)"""
        logger.info("=== TELJES SCRAPING TESZT (KORLÁTOZOTT) ===")
        
        try:
            # Weboldal struktúra
            structure = self.scraper.discover_website_structure()
            
            all_products = []
            
            # Minden kategóriából néhány termék
            for i, category_url in enumerate(structure['categories'][:3], 1):  # Csak első 3 kategória
                logger.info(f"Kategória {i}/3: {category_url}")
                
                category_products = self.scraper._scrape_category_products(category_url)
                
                # Limitálás
                category_products = category_products[:max_products_per_category]
                all_products.extend(category_products)
                
                logger.info(f"  Scraped: {len(category_products)} termék")
            
            # Direkt termék oldalak (limitált)
            for i, product_url in enumerate(structure['product_pages'][:5], 1):  # Csak első 5
                if product_url not in self.scraper.scraped_urls:
                    logger.info(f"Direkt termék {i}/5: {product_url}")
                    product = self.scraper._scrape_single_product(product_url)
                    if product:
                        all_products.append(product)
            
            logger.info(f"Összesen scraped termékek: {len(all_products)}")
            
            # Teljes validálás
            validation_report = self.validator.get_validation_report(all_products)
            logger.info(f"Validálási jelentés: {validation_report['summary']}")
            
            # Eredmények mentése
            self._save_full_results(all_products, validation_report)
            
            # Scraper statisztikák
            stats = self.scraper.get_scraping_statistics()
            logger.info(f"Scraper statisztikák: {stats}")
            
            return all_products
            
        except Exception as e:
            logger.error(f"Hiba a teljes scraping során: {e}")
            return []
    
    def _save_product_sample(self, product):
        """Minta termék mentése"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sample_product_{timestamp}.json"
        filepath = self.results_dir / filename
        
        product_data = {
            'name': product.name,
            'url': product.url,
            'category': product.category,
            'description': product.description,
            'technical_specs': product.technical_specs,
            'images': product.images,
            'documents': product.documents,
            'price': product.price,
            'availability': product.availability,
            'scraped_at': product.scraped_at.isoformat() if product.scraped_at else None
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(product_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Minta termék mentve: {filepath}")
    
    def _save_category_results(self, products, category_url):
        """Kategória eredmények mentése"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"category_results_{timestamp}.json"
        filepath = self.results_dir / filename
        
        results = {
            'category_url': category_url,
            'scraped_at': datetime.now().isoformat(),
            'product_count': len(products),
            'products': []
        }
        
        for product in products:
            results['products'].append({
                'name': product.name,
                'url': product.url,
                'category': product.category,
                'description': product.description[:200] + '...' if len(product.description) > 200 else product.description,
                'technical_specs_count': len(product.technical_specs),
                'images_count': len(product.images),
                'documents_count': len(product.documents)
            })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Kategória eredmények mentve: {filepath}")
    
    def _save_full_results(self, products, validation_report):
        """Teljes eredmények mentése"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"full_scraping_results_{timestamp}.json"
        filepath = self.results_dir / filename
        
        results = {
            'scraped_at': datetime.now().isoformat(),
            'total_products': len(products),
            'validation_report': validation_report,
            'products': []
        }
        
        for product in products:
            results['products'].append({
                'name': product.name,
                'url': product.url,
                'category': product.category,
                'description_length': len(product.description),
                'technical_specs_count': len(product.technical_specs),
                'images_count': len(product.images),
                'documents_count': len(product.documents)
            })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Teljes eredmények mentve: {filepath}")


def main():
    """Fő teszt funkció"""
    logger.info("Rockwool Scraper Teszt Indítása")
    logger.info("=" * 50)
    
    tester = ScraperTester()
    
    try:
        # 1. Weboldal struktúra teszt
        structure = tester.test_website_discovery()
        if not structure:
            logger.error("Weboldal struktúra teszt sikertelen - kilépés")
            return
        
        # 2. Egyetlen termék teszt
        sample_product = tester.test_single_product_scraping()
        if not sample_product:
            logger.error("Egyetlen termék teszt sikertelen")
        
        # 3. Kategória teszt
        category_products = tester.test_category_scraping(max_products=2)
        if not category_products:
            logger.error("Kategória teszt sikertelen")
        
        # 4. Teljes scraping teszt (korlátozott)
        all_products = tester.test_full_scraping(max_products_per_category=1)
        
        logger.info("=" * 50)
        logger.info("TESZT BEFEJEZVE")
        logger.info(f"Összesen tesztelt termékek: {len(all_products)}")
        logger.info(f"Eredmények mappája: {tester.results_dir}")
        
    except KeyboardInterrupt:
        logger.info("Teszt megszakítva felhasználó által")
    except Exception as e:
        logger.error(f"Váratlan hiba a teszt során: {e}")


if __name__ == "__main__":
    main() 