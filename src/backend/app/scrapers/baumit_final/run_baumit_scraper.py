#!/usr/bin/env python3
"""
BAUMIT Scraper Runner
--------------------

Purpose:
Simple runner script to execute BAUMIT scrapers based on priority.

Usage:
    python run_baumit_scraper.py catalog     # High Priority: A-Z catalog
    python run_baumit_scraper.py colors      # Medium Priority: Color systems
    python run_baumit_scraper.py all         # All scrapers
"""
import sys
import asyncio
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_catalog_scraper():
    """Run the high priority catalog scraper."""
    logger.info("🔴 Starting HIGH Priority: BAUMIT A-Z Catalog Scraper")
    try:
        from baumit_product_catalog_scraper import run as run_catalog
        await run_catalog()
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
    except Exception as e:
        logger.error(f"❌ Catalog scraper error: {e}")


async def run_color_scraper():
    """Run the medium priority color system scraper."""
    logger.info("🟡 Starting MEDIUM Priority: BAUMIT Color System Scraper")
    try:
        from baumit_color_system_scraper import run as run_colors
        await run_colors()
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
    except Exception as e:
        logger.error(f"❌ Color scraper error: {e}")


async def main():
    """Main runner function."""
    if len(sys.argv) < 2:
        print("Usage: python run_baumit_scraper.py [catalog|colors|all]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    logger.info("=== BAUMIT Scraper Runner ===")
    logger.info(f"Command: {command}")
    
    if command == "catalog":
        await run_catalog_scraper()
    elif command == "colors":
        await run_color_scraper()
    elif command == "all":
        await run_catalog_scraper()
        await run_color_scraper()
    else:
        logger.error(f"❌ Unknown command: {command}")
        print("Available commands: catalog, colors, all")
        sys.exit(1)
    
    logger.info("=== BAUMIT Scraper Runner Finished ===")

if __name__ == "__main__":
    asyncio.run(main()) 