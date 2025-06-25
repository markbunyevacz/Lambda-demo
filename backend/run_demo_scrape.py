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
from app.scraper.rockwool_scraper import RockwoolScraper
from app.scraper.database_integration import save_product_for_demo

# Alapvető logging konfiguráció
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def run_rockwool_scrape():
    """Lefuttatja a Rockwool scraper-t és menti az adatokat."""
    logging.info("--- Rockwool Scraper Indítása ---")
    
    try:
        # 1. Scraper indítása async context manager-rel
        async with RockwoolScraper() as scraper:
            # 2. Adatok begyűjtése
            logging.info("Termékek begyűjtése a Rockwool.com/hu oldalról...")
            scraped_products = await scraper.scrape_for_demo()
            logging.info(f"Begyűjtött termékek száma: {len(scraped_products)}")

            # 3. Adatok mentése az adatbázisba
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
        logging.error(f"Hiba történt a Rockwool scraping során: {e}", exc_info=True)

    logging.info("--- Rockwool Scraper Befejeződött ---")


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