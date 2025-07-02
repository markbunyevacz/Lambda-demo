import asyncio
import aiohttp
import aiofiles
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
import logging
import re
import os

# --- Configuration ---
BASE_URL = "https://www.leier.hu"
DOWNLOAD_DIR = Path(__file__).resolve().parents[4] / "downloads" / "leier_datasheets"
MAX_CONCURRENT_DOWNLOADS = 10

# Hardcoded list of high-priority PDF documents
PDF_URLS = [
    "https://www.leier.hu/storage/files/shares/downloads/leier_arlista_2024_tavasz_nyar_v3_compressed.pdf",
    "https://www.leier.hu/storage/files/shares/downloads/kaiserstein_arlista_2024_tavasz_nyar_v3_compressed.pdf",
    "https://www.leier.hu/storage/files/shares/downloads/Leier-teljesitmenynyilatkozatok/leierplan_falazoelemek_teljesitmenynyilatkozat_hu.pdf",
    "https://www.leier.hu/storage/files/shares/downloads/Leier-teljesitmenynyilatkozatok/duridur_es_durisoli_falazoelemek_teljesitmenynyilatkozat_hu.pdf"
]

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sanitize_filename(filename):
    """Sanitizes a filename by removing invalid characters."""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

async def download_pdf(session, url, download_folder):
    """Downloads a single PDF file asynchronously."""
    try:
        async with session.get(url) as response:
            if response.status == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
                filename = sanitize_filename(url.split('/')[-1])
                file_path = download_folder / filename
                
                if file_path.exists():
                    logger.info(f"File already exists, skipping: {filename}")
                    return

                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(await response.read())
                logger.info(f"Successfully downloaded: {filename}")
            else:
                logger.warning(f"Failed to download {url}. Status: {response.status}, Content-Type: {response.headers.get('Content-Type')}")
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")

async def get_category_links(session, url):
    """Gets all product category links from a starting URL."""
    category_links = set()
    try:
        async with session.get(url) as response:
            if response.status == 200:
                soup = BeautifulSoup(await response.text(), 'html.parser')
                # This selector needs to be adjusted based on the actual page structure
                for link in soup.select("a.product-card-link"): # Example selector
                    href = link.get('href')
                    if href:
                        category_links.add(urljoin(BASE_URL, href))
            else:
                logger.error(f"Failed to fetch category page {url}. Status: {response.status}")
    except Exception as e:
        logger.error(f"Error fetching category page {url}: {e}")
    return list(category_links)

async def main():
    """Main function to scrape and download PDFs."""
    logger.info("Starting Leier PDF scraper with direct links...")
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    
    all_pdf_links = set(PDF_URLS)

    async with aiohttp.ClientSession() as session:
        logger.info(f"Found {len(all_pdf_links)} unique PDF links to download.")

        tasks = [download_pdf(session, pdf_url, DOWNLOAD_DIR) for pdf_url in all_pdf_links]
        
        # Limit concurrency
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
        async def run_with_semaphore(task):
            async with semaphore:
                await task

        await asyncio.gather(*(run_with_semaphore(task) for task in tasks))

    logger.info("Scraping complete.")

if __name__ == "__main__":
    asyncio.run(main()) 