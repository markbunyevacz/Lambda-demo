#!/usr/bin/env python3
"""
LEIER Specific URLs Scraper
===========================

This scraper targets specific LEIER URLs provided by the user:
- Direct file server: https://www.leier.hu/uploads/files/
- Product pages: https://www.leier.hu/hu/termekek/leier-beton-pillerzsaluzo-elem-25
- Category pages: https://www.leier.hu/hu/termekeink/pillerzsaluzo-elem
- Main products: https://www.leier.hu/hu/termekeink
"""

import asyncio
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Set, Optional, Tuple, List
from urllib.parse import urljoin, urlparse

import aiofiles
import httpx
from bs4 import BeautifulSoup

# --- Configuration ---
BASE_URL = "https://www.leier.hu"

# Target URLs from user request
TARGET_URLS = [
    "https://www.leier.hu/uploads/files/",
    "https://www.leier.hu/hu/termekek/leier-beton-pillerzsaluzo-elem-25",
    "https://www.leier.hu/hu/termekeink/pillerzsaluzo-elem",
    "https://www.leier.hu/hu/termekeink/beton-zsaluzoelemek",
    "https://www.leier.hu/hu/termekeink"
]

class LeierSpecificUrlsScraper:
    """Scrapes specific LEIER URLs for downloadable content."""

    def __init__(self, test_mode: bool = False, max_concurrent: int = 5):
        self.test_mode = test_mode
        self.session_semaphore = asyncio.Semaphore(max_concurrent)
        
        # Setup paths
        current_dir = Path(__file__).resolve()
        project_root = current_dir.parents[3]
        self.base_dir = project_root / "src" / "downloads" / "leier_specific_urls"
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
        self.discovered_docs: Set[Tuple[str, str, str]] = set()  # (url, title, source)
        self.downloaded_files = set()
        self.failed_downloads = []
        self.duplicate_files = set()
        self.processed_urls = set()

        self.setup_logging()

    def setup_logging(self):
        """Sets up logging for the scraper."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.reports_dir / f'leier_specific_urls_{timestamp}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("🚀 LEIER Specific URLs Scraper Initialized")

    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetches HTML content from a URL."""
        try:
            async with self.session_semaphore:
                timeout = httpx.Timeout(45.0)
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                }
                async with httpx.AsyncClient(timeout=timeout, 
                                           headers=headers,
                                           follow_redirects=True) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response.text
        except Exception as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return None

    def extract_documents_from_html(self, html: str, source_url: str) -> List[Tuple[str, str]]:
        """Extracts document URLs from HTML content."""
        soup = BeautifulSoup(html, 'html.parser')
        documents = []

        # Comprehensive selectors for different types of document links
        selectors = [
            'a[href$=".pdf"]',  # Direct PDF links
            'a[href*=".pdf"]',  # PDF links with parameters
            'a[href*="/uploads/files/"]',  # File server links
            'a[href*="dokumentumtar"]',  # Document archive links
            'a[href*="download"]',  # Download links
            '.document-link a',  # Document containers
            '.related-documents a',  # Related documents section
            '.file-link a',  # File link containers
            'div[class*="document"] a',  # Document div containers
            '[class*="pdf"] a',  # PDF-related classes
            '[data-file] a',  # File data attributes
        ]

        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href', '')
                if href:
                    href_str = str(href)
                    if ('.pdf' in href_str.lower() or 
                       '/uploads/files/' in href_str or 
                       'dokumentumtar' in href_str or
                       'download' in href_str.lower()):
                        
                        # Make absolute URL
                        full_url = urljoin(BASE_URL, href_str)
                        
                        # Extract document title
                        title = link.get_text(strip=True) or link.get('title', '')
                        if not title:
                            # Try to extract from href
                            title = Path(urlparse(href_str).path).stem
                            if not title:
                                title = f"document_{len(documents)}"
                        
                        if full_url not in [d[0] for d in documents]:
                            documents.append((full_url, title))

        # Also look for documents in script tags (JavaScript-loaded content)
        scripts = soup.find_all('script')
        for script in scripts:
            if hasattr(script, 'string') and script.string:
                # Look for PDF URLs and file URLs in JavaScript
                patterns = [
                    r'["\']([^"\']*\.pdf[^"\']*)["\']',
                    r'["\']([^"\']*uploads/files/[^"\']*)["\']',
                    r'["\']([^"\']*dokumentumtar[^"\']*)["\']'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, script.string)
                    for match in matches:
                        full_url = urljoin(BASE_URL, match)
                        title = Path(urlparse(match).path).stem or f"script_doc_{len(documents)}"
                        if full_url not in [d[0] for d in documents]:
                            documents.append((full_url, title))

        # Look for file listings in tables or lists (for uploads/files/ directory)
        if '/uploads/files/' in source_url:
            # Look for file listings
            file_patterns = [
                'a[href$=".pdf"]',
                'a[href$=".doc"]',
                'a[href$=".docx"]',
                'a[href$=".zip"]',
                'a[href$=".dwg"]',
                'a[href$=".dxf"]'
            ]
            
                         for pattern in file_patterns:
                 file_links = soup.select(pattern)
                 for link in file_links:
                     href = link.get('href', '')
                     if href:
                         href_str = str(href)
                         full_url = urljoin(source_url, href_str)
                         title = link.get_text(strip=True) or Path(href_str).name
                         if full_url not in [d[0] for d in documents]:
                             documents.append((full_url, title))

        self.logger.info(f"Found {len(documents)} documents at {source_url}")
        return documents

    def extract_product_links(self, html: str, source_url: str) -> List[str]:
        """Extracts product page links from category pages."""
        soup = BeautifulSoup(html, 'html.parser')
        product_links = []

        # Look for product links
        selectors = [
            'a[href*="/termekek/"]',  # Direct product links
            'a[href*="/hu/termekek/"]',  # Full product links
            '.product-item a',  # Product item containers
            '.card a',  # Card-based layouts
            'div[class*="product"] a'  # Product div containers
        ]

        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href', '')
                if href and '/termekek/' in href:
                    full_url = urljoin(BASE_URL, href)
                    if full_url not in product_links:
                        product_links.append(full_url)

        self.logger.info(f"Found {len(product_links)} product links at {source_url}")
        return product_links

    async def download_document(self, url: str, title: str, source: str):
        """Downloads a document with organized folder structure."""
        # Sanitize source for folder name
        source_name = urlparse(source).path.strip('/').replace('/', '_')
        if not source_name:
            source_name = "root"
        
        # Create source-specific folder
        source_dir = self.directories['documents'] / source_name
        source_dir.mkdir(exist_ok=True)
        
        # Sanitize filename
        safe_title = re.sub(r'[^\w\s\-\.]', '_', title)
        if not safe_title.lower().endswith(('.pdf', '.doc', '.docx', '.zip', '.dwg', '.dxf')):
            # Try to determine extension from URL
            parsed_url = urlparse(url)
            url_path = parsed_url.path
            if '.' in url_path:
                ext = Path(url_path).suffix
                safe_title += ext
            else:
                safe_title += '.pdf'  # Default to PDF
        
        file_path = source_dir / safe_title

        if file_path.exists():
            self.logger.warning(f"Duplicate found, skipping: {safe_title}")
            self.duplicate_files.add(url)
            return

        try:
            async with self.session_semaphore:
                headers = {'Referer': BASE_URL}
                timeout = httpx.Timeout(120.0)
                async with httpx.AsyncClient(timeout=timeout, 
                                           headers=headers) as client:
                    response = await client.get(url)
                    response.raise_for_status()

                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(response.content)
                
                self.logger.info(f"✅ Downloaded: {source_name}/{safe_title}")
                self.downloaded_files.add(url)
        except Exception as e:
            self.logger.error(f"❌ Failed to download {url}: {e}")
            self.failed_downloads.append((url, str(e)))

    async def scrape_url(self, url: str):
        """Scrapes a specific URL for downloadable content."""
        if url in self.processed_urls:
            return

        self.logger.info(f"--- Scraping URL: {url} ---")
        html = await self.fetch_page(url)
        if not html:
            return

        # Save page HTML for debugging
        url_name = urlparse(url).path.strip('/').replace('/', '_')
        if not url_name:
            url_name = "root"
        page_file = self.directories['page_samples'] / f"{url_name}.html"
        async with aiofiles.open(page_file, 'w', encoding='utf-8') as f:
            await f.write(html)

        # Extract documents from this page
        documents = self.extract_documents_from_html(html, url)
        for doc_url, doc_title in documents:
            self.discovered_docs.add((doc_url, doc_title, url))

        # If this is a category page, also scrape product pages
        if '/termekeink/' in url and url != "https://www.leier.hu/hu/termekeink":
            product_links = self.extract_product_links(html, url)
            for product_url in product_links[:5]:  # Limit to first 5 products for testing
                await self.scrape_url(product_url)
                await asyncio.sleep(0.5)  # Rate limiting

        self.processed_urls.add(url)

    async def run(self):
        """Main execution logic for the specific URLs scraper."""
        start_time = datetime.now()
        self.logger.info("--- Starting LEIER Specific URLs Scraping ---")

        # Process each target URL
        for url in TARGET_URLS:
            await self.scrape_url(url)
            await asyncio.sleep(1)  # Rate limiting between URLs

        # Download all discovered documents
        if self.test_mode:
            self.logger.info("Test mode enabled. Skipping downloads.")
        elif self.discovered_docs:
            self.logger.info(f"--- Downloading {len(self.discovered_docs)} documents ---")
            tasks = [self.download_document(url, title, source) 
                    for url, title, source in self.discovered_docs]
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            self.logger.warning("No documents discovered to download.")

        self.generate_report(start_time)

    def generate_report(self, start_time: datetime):
        """Generates and saves a JSON report of the scraping run."""
        report = {
            "run_timestamp": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "test_mode": self.test_mode,
            "target_urls": TARGET_URLS,
            "summary": {
                "urls_processed": len(self.processed_urls),
                "documents_discovered": len(self.discovered_docs),
                "downloads_successful": len(self.downloaded_files),
                "downloads_failed": len(self.failed_downloads),
                "duplicates_found": len(self.duplicate_files),
            },
            "discovered_docs_sample": [
                {"url": url, "title": title, "source": source} 
                for url, title, source in list(self.discovered_docs)[:20]
            ],
            "failed_downloads": self.failed_downloads,
        }
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'leier_specific_urls_report_{timestamp}.json'
        report_path = self.reports_dir / filename
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
        self.logger.info(f"📊 Report saved to {report_path}")


async def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="LEIER Specific URLs Scraper"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (discover links but do not download).",
    )
    args = parser.parse_args()

    scraper = LeierSpecificUrlsScraper(test_mode=args.test)
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main()) 