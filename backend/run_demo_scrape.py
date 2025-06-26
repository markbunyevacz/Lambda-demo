"""
DEMO Scraper Indító Szkript
---------------------------

Ez a szkript felelős a DEMO adatgyűjtési folyamatának elindításáért.
Sorban meghívja a scraper-eket, és az eredményeket elmenti az adatbázisba
a DEMO-ra optimalizált `save_product_for_demo` funkció segítségével.
"""

import asyncio
import logging
from app.database import SessionLocal
from app.scraper.rockwool_scraper import RockwoolApiScraper
from app.scraper.database_integration import save_product_for_demo

# Alapvető logging konfiguráció
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def run_rockwool_scrape():
    """Lefuttatja a Rockwool API-alapú PDF scraper-t és menti az adatokat."""
    logging.info("--- Rockwool API Scraper Indítása ---")
    
    scraper = RockwoolApiScraper()
    try:
        # 1. Adatok begyűjtése az új, API-alapú metódussal (limitálva az első 5-re)
        scraped_products = await scraper.scrape_all_product_datasheets(limit=5)
        logging.info(f"Begyűjtött PDF-alapú termékek száma: {len(scraped_products)}")

        # 2. Adatok mentése az adatbázisba
        if scraped_products:
            logging.info("Termékek mentése az adatbázisba...")
            db = SessionLocal()
            try:
                for i, product_data in enumerate(scraped_products):
                    logging.info(f"Mentés: {i+1}/{len(scraped_products)} - {product_data['name']}")
                    save_product_for_demo(db, product_data, "ROCKWOOL")
                logging.info("Adatbázis mentés sikeresen befejeződött.")
            finally:
                db.close()
        
    except Exception as e:
        logging.error(f"Hiba történt a Rockwool API scraping során: {e}", exc_info=True)

    logging.info("--- Rockwool API Scraper Befejeződött ---")


async def main():
    """A fő DEMO adatgyűjtő folyamat."""
    logging.info("===== DEMO ADATGYŰJTÉSI FOLYAMAT INDUL =====")
    
    await run_rockwool_scrape()
    
    # Ide kerülnek majd a további scraper-ek (Leier, Baumit) hívásai
    # await run_leier_scrape()
    # await run_baumit_scrape()
    
    logging.info("===== DEMO ADATGYŰJTÉSI FOLYAMAT BEFEJEZŐDÖTT =====")


if __name__ == "__main__":
    asyncio.run(main()) 