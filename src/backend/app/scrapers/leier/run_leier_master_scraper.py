#!/usr/bin/env python3
"""
LEIER Master Scraper Coordinator
================================

This script orchestrates the three most effective LEIER scrapers to ensure
the most comprehensive data collection possible. It runs them sequentially.

1.  **Recursive API Scraper**: Gets all documents from the backend documents API.
2.  **Product Tree Mapper**: Scrapes all product pages and their specific documents.
3.  **Download Manager Scraper**: Fetches files from the separate download manager system.
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add current directory to path for local imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

try:
    from leier_recursive_scraper import LeierRecursiveScraper
    from leier_product_tree_mapper import LeierProductTreeMapper
    from leier_download_manager_scraper import LeierDownloadManagerScraper
except ImportError as e:
    logger.error(f"Failed to import LEIER scrapers: {e}")
    logger.error("Make sure all required scraper files are in the same directory.")
    sys.exit(1)


class LeierMasterCoordinator:
    """Coordinates the most effective LEIER scraping activities."""

    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        self.start_time = datetime.now()
        logger.info("🚀 LEIER Master Scraping Coordinator Initialized")
        if self.test_mode:
            logger.info("🧪 Running in TEST MODE - downloads will be skipped where supported.")

    async def run_all(self):
        """Runs all three primary scrapers in sequence."""
        logger.info("=" * 70)
        logger.info("Executing COMPLETE LEIER Data Collection")
        logger.info("This will run the three most effective scrapers.")
        logger.info("=" * 70)

        # 1. Recursive API Scraper
        try:
            logger.info("\n--- STAGE 1: Running Recursive API Scraper ---")
            recursive_scraper = LeierRecursiveScraper(test_mode=self.test_mode)
            await recursive_scraper.run()
            logger.info("--- STAGE 1: Recursive API Scraper COMPLETE ---")
        except Exception as e:
            logger.error(f"❌ Critical error in Recursive API Scraper: {e}", exc_info=True)

        await asyncio.sleep(5)  # Brief pause between stages

        # 2. Product Tree Mapper
        try:
            logger.info("\n--- STAGE 2: Running Product Tree Mapper ---")
            # Note: This scraper does not have a test mode. It always downloads.
            product_tree_scraper = LeierProductTreeMapper()
            await product_tree_scraper.run()
            logger.info("--- STAGE 2: Product Tree Mapper COMPLETE ---")
        except Exception as e:
            logger.error(f"❌ Critical error in Product Tree Mapper: {e}", exc_info=True)

        await asyncio.sleep(5)  # Brief pause between stages

        # 3. Download Manager Scraper
        try:
            logger.info("\n--- STAGE 3: Running Download Manager Scraper ---")
            download_manager_scraper = LeierDownloadManagerScraper(test_mode=self.test_mode)
            await download_manager_scraper.run()
            logger.info("--- STAGE 3: Download Manager Scraper COMPLETE ---")
        except Exception as e:
            logger.error(f"❌ Critical error in Download Manager Scraper: {e}", exc_info=True)

        self.generate_final_summary()

    def generate_final_summary(self):
        """Prints a final summary of the master coordinator's run."""
        duration = (datetime.now() - self.start_time).total_seconds()
        logger.info("\n" + "=" * 70)
        logger.info("📊 LEIER MASTER COORDINATOR - FINAL SUMMARY")
        logger.info("=" * 70)
        logger.info("All scraping stages have been executed.")
        logger.info(f"⏱️  Total Duration: {duration:.1f} seconds")
        logger.info("Please check the individual reports from each scraper in the 'leier_scraping_reports' directory for detailed results.")
        logger.info("Downloaded files are organized in the following directories inside 'downloads/':")
        logger.info("  - leier_datasheets/ (from Recursive API Scraper)")
        logger.info("  - leier_products_complete/ (from Product Tree Mapper)")
        logger.info("  - leier_download_manager/ (from Download Manager Scraper)")
        logger.info("=" * 70)


async def main():
    """Main entry point for LEIER master scraper coordinator."""
    parser = argparse.ArgumentParser(description="LEIER Master Scraper Coordinator")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run scrapers in test mode where applicable (skips downloads).",
    )
    args = parser.parse_args()

    coordinator = LeierMasterCoordinator(test_mode=args.test)
    await coordinator.run_all()


if __name__ == "__main__":
    asyncio.run(main()) 