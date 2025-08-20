#!/usr/bin/env python3
"""
LEIER Download Manager Scraper
==============================

This scraper targets the Leier 'Download Manager' system hosted on the
`u-ertek-kalkulator.leier.hu` subdomain. It is designed to extract
technical documents, CAD files, and other materials not available through
the main website's document library.

**Key Features:**
- Targets `u-ertek-kalkulator.leier.hu/downloadmanager/`
- Discovers documents from known entry points like `/letoltesek-1`
- Handles the `/index/id/[ID]/m/[MODULE]` URL structure
- Downloads files into a dedicated `leier_download_manager` directory
- Operates independently from other Leier scrapers
"""

import asyncio
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Set, Optional, Tuple, List, Any
from urllib.parse import urljoin, urlparse

import aiofiles
import httpx
from bs4 import BeautifulSoup

# --- Configuration ---
BASE_URL = "https://u-ertek-kalkulator.leier.hu"
START_URLS = [
    "https://u-ertek-kalkulator.leier.hu/letoltesek-1",
    "https://u-ertek-kalkulator.leier.hu/alkalmazastechnikak",
    "https://u-ertek-kalkulator.leier.hu/teljesitmenynyilatkozat",
]


class LeierDownloadManagerScraper:
    """Scrapes the LEIER Download Manager system."""

    def __init__(self, test_mode: bool = False, max_concurrent: int = 5):
        self.test_mode = test_mode
        self.session_semaphore = asyncio.Semaphore(max_concurrent)

        # Setup paths
        current_dir = Path(__file__).resolve().parent
        # Correctly navigate to the project root (Lambda/)
        project_root = current_dir.parents[4] 
        self.base_dir = project_root / "downloads" / "leier_download_manager"
        self.reports_dir = project_root / "leier_scraping_reports"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Storage directories
        self.directories = {
            'documents': self.base_dir / 'documents',
            'duplicates': self.base_dir / 'duplicates',
            'page_samples': self.base_dir / 'page_samples'
        }
        for directory in self.directories.values():
            directory.mkdir(parents=True, exist_ok=True)

        # Tracking
        self.discovered_links: Set[Tuple[str, str]] = set()  # (url, title)
        self.downloaded_files: Set[str] = set()
        self.failed_downloads: List[Tuple[str, str]] = []
        self.duplicate_files: Set[str] = set()
        self.processed_urls: Set[str] = set()

        self.setup_logging()

    def setup_logging(self):
        """Sets up logging for the scraper."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.reports_dir / f'leier_download_manager_{timestamp}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("🚀 LEIER Download Manager Scraper Initialized")

    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetches HTML content from a URL."""
        if url in self.processed_urls:
            return None
        self.processed_urls.add(url)
        
        self.logger.info(f"Fetching page: {url}")
        try:
            async with self.session_semaphore:
                timeout = httpx.Timeout(45.0)
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9,hu;q=0.8',
                    'Referer': 'https://u-ertek-kalkulator.leier.hu/'
                }
                async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response.text
        except Exception as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return None

    def extract_download_links(self, html: str, source_url: str) -> List[Tuple[str, str]]:
        """Extracts download links from a page."""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            # Target links pointing to the download manager or containing file extensions
            if '/downloadmanager/details/id/' in href or any(href.lower().endswith(ext) for ext in ['.pdf', '.dwg', '.zip']):
                full_url = urljoin(BASE_URL, href)
                title = a_tag.get_text(strip=True) or Path(urlparse(full_url).path).name
                if (full_url, title) not in self.discovered_links:
                    links.append((full_url, title))
                    self.discovered_links.add((full_url, title))
        
        self.logger.info(f"Found {len(links)} new download links on {source_url}")
        return links

    async def download_file(self, url: str, title: str):
        """Downloads a file into the documents directory."""
        # Sanitize title for filename
        safe_filename = re.sub(r'[^\w\s\.\-]', '_', title)
        file_ext = Path(urlparse(url).path).suffix
        if not safe_filename.lower().endswith(file_ext.lower()) and file_ext:
            safe_filename += file_ext

        if not safe_filename:
            safe_filename = Path(urlparse(url).path).name

        target_path = self.directories['documents'] / safe_filename

        if target_path.exists():
            self.logger.warning(f"File already exists, skipping: {safe_filename}")
            self.duplicate_files.add(url)
            return

        self.logger.info(f"Downloading: {title} from {url}")
        try:
            async with self.session_semaphore:
                async with httpx.AsyncClient(timeout=180.0, follow_redirects=True) as client:
                    response = await client.get(url)
                    response.raise_for_status()

                async with aiofiles.open(target_path, 'wb') as f:
                    await f.write(response.content)

                self.logger.info(f"✅ Downloaded: {safe_filename}")
                self.downloaded_files.add(url)

        except Exception as e:
            self.logger.error(f"❌ Failed to download {url}: {e}")
            self.failed_downloads.append((url, str(e)))

    async def scrape_entry_point(self, url: str):
        """Scrapes an entry point URL to discover download links."""
        html = await self.fetch_page(url)
        if html:
            self.extract_download_links(html, url)

    async def run(self):
        """Main execution logic for the scraper."""
        start_time = datetime.now()
        self.logger.info("--- Starting LEIER Download Manager Scraping ---")

        # Step 1: Discover all download links from entry points
        self.logger.info(f"Scraping {len(START_URLS)} entry points...")
        discovery_tasks = [self.scrape_entry_point(url) for url in START_URLS]
        await asyncio.gather(*discovery_tasks)
        
        self.logger.info(f"Discovery complete. Found {len(self.discovered_links)} unique document links.")

        # Step 2: Download all discovered files
        if self.test_mode:
            self.logger.info("Test mode enabled. Skipping downloads.")
        elif self.discovered_links:
            self.logger.info(f"--- Downloading {len(self.discovered_links)} documents ---")
            download_tasks = [self.download_file(url, title) for url, title in self.discovered_links]
            await asyncio.gather(*download_tasks)
        else:
            self.logger.warning("No documents to download.")
            
        self.generate_report(start_time)

    def generate_report(self, start_time: datetime):
        """Generates a JSON report of the scraping run."""
        report = {
            "run_timestamp": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "test_mode": self.test_mode,
            "start_urls": START_URLS,
            "summary": {
                "urls_processed": len(self.processed_urls),
                "documents_discovered": len(self.discovered_links),
                "downloads_successful": len(self.downloaded_files),
                "downloads_failed": len(self.failed_downloads),
                "duplicates_found": len(self.duplicate_files),
            },
            "discovered_docs_sample": list(self.discovered_links)[:20],
            "failed_downloads": self.failed_downloads,
        }
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.reports_dir / f'leier_download_manager_report_{timestamp}.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
        self.logger.info(f"📊 Report saved to {report_path}")

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="LEIER Download Manager Scraper")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (discover links but do not download).",
    )
    args = parser.parse_args()

    scraper = LeierDownloadManagerScraper(test_mode=args.test)
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main()) 