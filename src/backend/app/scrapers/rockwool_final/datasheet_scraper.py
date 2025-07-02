"""
Rockwool Datasheet Scraper (AI-Driven)
----------------------------------------

This script runs the Rockwool product datasheets scraper using the
BrightData MCP Agent. It targets the `termekadatlapok` (product datasheets)
page to extract individual product PDFs. It is designed to be run both as part
of the application (e.g., via Celery) and as a standalone script for testing.
"""
import asyncio
import logging
import sys
from pathlib import Path


# This check ensures that the 'app' module can be found when running as a script
if __name__ == "__main__" and (__package__ is None or "." not in __package__):
    # If run as a script, add the backend directory to the path.
    # This is a common pattern for making package modules runnable.
    backend_path = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(backend_path))

# The linter may not find this module, but the path modification above
# ensures it's available when run as a script or within the application.
from app.agents.brightdata_agent import BrightDataMCPAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- File System Configuration ---
# Use absolute path from project root to ensure consistency
PROJECT_ROOT = Path(__file__).resolve().parents[3]  # Go up to Lambda/ root
PDF_STORAGE_DIR = PROJECT_ROOT / "src" / "downloads" / "rockwool_datasheets"
DEBUG_FILE_PATH = PROJECT_ROOT / "debug_termekadatlapok.html"

# Ensure output directory exists
PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class RockwoolDirectScraper:
    """
    Scraper for Rockwool product datasheets using the BrightData MCP Agent.

    This version is integrated into the application structure.
    """
    def __init__(self):
        """Initializes the scraper."""
        self.logger = logging.getLogger(__name__)

    async def run(self):
        """Executes the entire scraping process."""
        self.logger.info("🎯 Starting Rockwool AI-Powered Datasheet Scraper...")
        
        try:
            # Initialize the BrightData MCP Agent
            agent = BrightDataMCPAgent()
            
            if not agent.mcp_available:
                self.logger.error(
                    "❌ BrightData MCP Agent is not available. "
                    "Check .env configuration."
                )
                return None
            
            # Target the product datasheets page
            target_url = ("https://www.rockwool.com/hu/muszaki-informaciok/"
                          "termekadatlapok/")
            self.logger.info("🎯 Targeting URL: %s", target_url)
            
            # AI-driven scraping task description
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
            self.logger.info("=" * 60)
            self.logger.info("🎯 ROCKWOOL PRODUCT SCRAPING RESULTS")
            self.logger.info("=" * 60)
            self.logger.info("📄 Products found: %s", len(products))
            
            if products:
                for i, product in enumerate(products, 1):
                    self.logger.info(
                        "📦 Product %d: %s", i, product.get('name', 'Unknown')
                    )
                    if product.get('category'):
                        self.logger.info(
                            "    Category: %s", product.get('category')
                        )
                    if product.get('pdf_url'):
                        self.logger.info("    PDF: %s", product.get('pdf_url'))
            
            # Get scraping statistics
            stats = agent.get_scraping_statistics()
            self.logger.info("=" * 60)
            self.logger.info("📊 SCRAPING STATISTICS")
            self.logger.info("=" * 60)
            self.logger.info(
                "✅ Successful scrapes: %s", stats.get('successful_scrapes', 0)
            )
            self.logger.info(
                "❌ Failed scrapes: %s", stats.get('failed_scrapes', 0)
            )
            self.logger.info(
                "📈 Success rate: %.1f%%", stats.get('success_rate', 0)
            )
            self.logger.info(
                "⏱️ Total requests: %s", stats.get('requests_made', 0)
            )
            self.logger.info("=" * 60)
            
            self.logger.info("✅ Rockwool AI-powered scraping completed!")
            return products
            
        except ImportError as e:
            self.logger.error(
                "❌ Failed to import a required module: %s. "
                "Check your python path.", e
            )
            raise
        except Exception as e:
            self.logger.error(
                "❌ An unexpected error occurred during scraping: %s",
                e,
                exc_info=True
            )
            raise


async def main():
    """Standalone runner for the scraper."""
    scraper = RockwoolDirectScraper()
    await scraper.run()


if __name__ == "__main__":
    # This block allows the script to be executed directly for testing.
    logger.info("🚀 Running Rockwool Datasheet Scraper in standalone mode...")
    asyncio.run(main())
