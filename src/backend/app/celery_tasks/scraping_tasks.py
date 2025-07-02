"""
Celery Tasks for Automated Data Collection
------------------------------------------
This module contains Celery tasks for running scrapers, which can be
triggered manually (e.g., via an API endpoint for a 'Refresh' button) or
on a schedule.
"""

import asyncio
import logging
from datetime import datetime

from celery import shared_task

# Import the scraper classes using relative paths
from ..scrapers.rockwool.datasheet_scraper import RockwoolDirectScraper
from ..scrapers.rockwool.brochure_and_pricelist_scraper import (
    RockwoolBrochureScraper,
)

logger = logging.getLogger(__name__)


@shared_task(name="tasks.run_datasheet_scraping")
def run_datasheet_scraping_task():
    """
    Celery task to run the Rockwool datasheet scraper.
    This can be called from an API endpoint to refresh product datasheets.
    """
    logger.info("▶️ Starting datasheet scraping task...")
    try:
        scraper = RockwoolDirectScraper()
        asyncio.run(scraper.run())
        logger.info("✅ Datasheet scraping task finished successfully.")
        return {"status": "success", "scraper": "datasheet"}
    except Exception as e:
        logger.error(f"❌ Datasheet scraping task failed: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}


@shared_task(name="tasks.run_brochure_scraping")
def run_brochure_scraping_task():
    """
    Celery task to run the Rockwool brochure and pricelist scraper.
    This can be called from an API endpoint to refresh documents.
    """
    logger.info("▶️ Starting brochure and pricelist scraping task...")
    try:
        scraper = RockwoolBrochureScraper()
        asyncio.run(scraper.run())
        logger.info(
            "✅ Brochure and pricelist scraping task finished successfully."
        )
        return {"status": "success", "scraper": "brochure_and_pricelist"}
    except Exception as e:
        logger.error(
            f"❌ Brochure and pricelist scraping task failed: {e}", exc_info=True
        )
        return {"status": "failed", "error": str(e)}


@shared_task(name="tasks.test_connection")
def test_scraper_connection():
    """
    A simple task to test the connection to the target website.
    """
    logger.info("▶️ Running connection test task...")
    try:
        import requests
        response = requests.get('https://www.rockwool.hu', timeout=10)
        response.raise_for_status()
        logger.info("✅ Connection test successful.")
        return {
            'status': 'success',
            'http_status': response.status_code,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        return {'status': 'failed', 'error': str(e)}


@shared_task
def get_scraping_queue_status():
    """
    Scraping feladatok queue státuszának lekérése.

    Returns:
        dict: Queue státusz információk.
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