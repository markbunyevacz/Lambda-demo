#!/usr/bin/env python3
"""
RockWool Product Scraper
------------------------
This script runs the RockWool product datasheets scraper using the BrightData MCP Agent.
It targets the termekadatlapok (product datasheets) page to extract individual product PDFs.
"""

# CRITICAL: Load environment variables FIRST, before ANY other imports
# that might create agent instances
from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
import sys
from pathlib import Path

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the backend to the Python path
backend_path = Path(__file__).parent / "src" / "backend"
sys.path.insert(0, str(backend_path))

# Now import the agent - environment should already be loaded
try:
    from app.agents.brightdata_agent import BrightDataMCPAgent
except ImportError as e:
    logger.error("Failed to import BrightDataMCPAgent. Check backend path.")
    logger.error(f"Import error: {e}")
    sys.exit(1)

async def main():
    """Main function to run the RockWool product scraper."""
    logger.info("🎯 Starting RockWool Product Datasheets Scraper...")
    
    try:
        # Initialize the BrightData MCP Agent
        agent = BrightDataMCPAgent()
        
        if not agent.mcp_available:
            logger.error("❌ BrightData MCP Agent is not available. Check .env configuration.")
            return
        
        # Target the product datasheets page
        target_url = "https://www.rockwool.com/hu/muszaki-informaciok/termekadatlapok/"
        logger.info(f"🎯 Targeting URL: {target_url}")
        
        # Run AI-driven scraping for product datasheets
        task_description = """
        Rockwool termékadatlapokat kell összegyűjteni a magyar weboldalról.
        Minden termékhez gyűjts össze:
        - Termék név és típus
        - Műszaki paraméterek (hővezetési tényező, tűzállóság, méretek)
        - Alkalmazási területek és kategória
        - PDF termékadatlap letöltési link
        - Termék leírás
        
        Keress minden elérhető terméket és azok PDF dokumentumait.
        """
        
        products = await agent.scrape_rockwool_with_ai(
            target_urls=[target_url], 
            task_description=task_description
        )
        
        # Log results
        logger.info("=" * 60)
        logger.info("🎯 ROCKWOOL PRODUCT SCRAPING RESULTS")
        logger.info("=" * 60)
        logger.info(f"📄 Products found: {len(products)}")
        
        if products:
            for i, product in enumerate(products, 1):
                logger.info(f"📦 Product {i}: {product.get('name', 'Unknown')}")
                if product.get('category'):
                    logger.info(f"    Category: {product.get('category')}")
                if product.get('pdf_url'):
                    logger.info(f"    PDF: {product.get('pdf_url')}")
        
        # Get scraping statistics
        stats = agent.get_scraping_statistics()
        logger.info("=" * 60)
        logger.info("📊 SCRAPING STATISTICS")
        logger.info("=" * 60)
        logger.info(f"✅ Successful scrapes: {stats.get('successful_scrapes', 0)}")
        logger.info(f"❌ Failed scrapes: {stats.get('failed_scrapes', 0)}")
        logger.info(f"📈 Success rate: {stats.get('success_rate', 0):.1f}%")
        logger.info(f"⏱️  Total requests: {stats.get('requests_made', 0)}")
        logger.info("=" * 60)
        
        logger.info("✅ RockWool product scraping completed!")
        
    except Exception as e:
        logger.error(f"❌ Error during scraping: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 