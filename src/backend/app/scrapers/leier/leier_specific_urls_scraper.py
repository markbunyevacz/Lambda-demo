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
from typing import Set, Optional, Tuple, List
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
        self.downloaded_files: Set[str] = set()
        self.failed_downloads: List[Tuple[str, str]] = []
        self.duplicate_files: Set[str] = set()
        self.processed_urls: Set[str] = set()

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
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                  'AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;'
                              'q=0.9,*/*;q=0.8'
                }
                async with httpx.AsyncClient(
                    timeout=timeout, 
                    headers=headers,
                    follow_redirects=True
                ) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response.text
        except Exception as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return None

    def _get_document_selectors(self) -> List[str]:
        """Returns CSS selectors for different types of document links."""
        return [
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

    def _is_valid_document_link(self, href_str: str) -> bool:
        """Checks if a link is a valid document link."""
        return (
            '.pdf' in href_str.lower() or 
            '/uploads/files/' in href_str or 
            'dokumentumtar' in href_str or
            'download' in href_str.lower()
        )

    def _extract_document_title(self, link, href_str: str, doc_count: int) -> str:
        """Extracts document title from link element."""
        title = link.get_text(strip=True) or link.get('title', '')
        if not title:
            # Try to extract from href
            title = Path(urlparse(href_str).path).stem
            if not title:
                title = f"document_{doc_count}"
        return title

    def _extract_documents_from_css_selectors(
        self, soup: BeautifulSoup
    ) -> List[Tuple[str, str]]:
        """Extracts documents using CSS selectors."""
        documents = []
        selectors = self._get_document_selectors()

        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href', '')
                if not href:
                    continue
                    
                href_str = str(href)
                if not self._is_valid_document_link(href_str):
                    continue
                
                # Make absolute URL
                full_url = urljoin(BASE_URL, href_str)
                
                # Extract document title
                title = self._extract_document_title(
                    link, href_str, len(documents)
                )
                
                # Avoid duplicates
                if full_url not in [d[0] for d in documents]:
                    documents.append((full_url, title))

        return documents

    def _get_script_patterns(self) -> List[str]:
        """Returns regex patterns for finding documents in JavaScript."""
        return [
            r'["\']([^"\']*\.pdf[^"\']*)["\']',
            r'["\']([^"\']*uploads/files/[^"\']*)["\']',
            r'["\']([^"\']*dokumentumtar[^"\']*)["\']'
        ]

    def _extract_documents_from_scripts(
        self, soup: BeautifulSoup
    ) -> List[Tuple[str, str]]:
        """Extracts documents from JavaScript content."""
        documents = []
        scripts = soup.find_all('script')
        patterns = self._get_script_patterns()
        
        for script in scripts:
            if not (hasattr(script, 'string') and script.string):
                continue
                
            for pattern in patterns:
                matches = re.findall(pattern, script.string)
                for match in matches:
                    full_url = urljoin(BASE_URL, match)
                    title = (
                        Path(urlparse(match).path).stem or 
                        f"script_doc_{len(documents)}"
                    )
                    
                    # Avoid duplicates
                    if full_url not in [d[0] for d in documents]:
                        documents.append((full_url, title))

        return documents

    def _get_file_patterns(self) -> List[str]:
        """Returns file extension patterns for file listings."""
        return [
            'a[href$=".pdf"]',
            'a[href$=".doc"]',
            'a[href$=".docx"]',
            'a[href$=".zip"]',
            'a[href$=".dwg"]',
            'a[href$=".dxf"]'
        ]

    def _is_file_server_url(self, source_url: str) -> bool:
        """Checks if URL is a file server URL."""
        return '/uploads/files/' in source_url

    def _extract_documents_from_file_listings(
        self, soup: BeautifulSoup, source_url: str
    ) -> List[Tuple[str, str]]:
        """Extracts documents from file server listings."""
        documents = []
        
        if not self._is_file_server_url(source_url):
            return documents
            
        file_patterns = self._get_file_patterns()
        
        for pattern in file_patterns:
            file_links = soup.select(pattern)
            for link in file_links:
                href = link.get('href', '')
                if not href:
                    continue
                    
                href_str = str(href)
                full_url = urljoin(source_url, href_str)
                title = (
                    link.get_text(strip=True) or Path(href_str).name
                )
                
                # Avoid duplicates
                if full_url not in [d[0] for d in documents]:
                    documents.append((full_url, title))

        return documents

    def extract_documents_from_html(
        self, html: str, source_url: str
    ) -> List[Tuple[str, str]]:
        """Extracts document URLs from HTML content."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract documents from different sources
        css_documents = self._extract_documents_from_css_selectors(soup)
        script_documents = self._extract_documents_from_scripts(soup)
        file_documents = self._extract_documents_from_file_listings(
            soup, source_url
        )
        
        # Combine all documents and remove duplicates
        all_documents = css_documents + script_documents + file_documents
        unique_documents = []
        seen_urls = set()
        
        for url, title in all_documents:
            if url not in seen_urls:
                unique_documents.append((url, title))
                seen_urls.add(url)

        self.logger.info(
            f"Found {len(unique_documents)} documents at {source_url}"
        )
        return unique_documents

    def _get_product_link_selectors(self) -> List[str]:
        """Returns CSS selectors for product links."""
        return [
            'a[href*="/termekek/"]',  # Direct product links
            'a[href*="/hu/termekek/"]',  # Full product links
            '.product-item a',  # Product item containers
            '.card a',  # Card-based layouts
            'div[class*="product"] a'  # Product div containers
        ]

    def _is_valid_product_link(self, href: str) -> bool:
        """Checks if a link is a valid product link."""
        return href and '/termekek/' in href

    def extract_product_links(
        self, html: str, source_url: str
    ) -> List[str]:
        """Extracts product page links from category pages."""
        soup = BeautifulSoup(html, 'html.parser')
        product_links = []
        selectors = self._get_product_link_selectors()

        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href', '')
                if not self._is_valid_product_link(href):
                    continue
                    
                full_url = urljoin(BASE_URL, href)
                if full_url not in product_links:
                    product_links.append(full_url)

        self.logger.info(
            f"Found {len(product_links)} product links at {source_url}"
        )
        return product_links

    def _sanitize_source_name(self, source: str) -> str:
        """Sanitizes source URL for use as folder name."""
        source_name = urlparse(source).path.strip('/').replace('/', '_')
        return source_name if source_name else "root"

    def _determine_file_extension(self, url: str, title: str) -> str:
        """Determines file extension from URL or defaults to PDF."""
        extensions = ('.pdf', '.doc', '.docx', '.zip', '.dwg', '.dxf')
        if title.lower().endswith(extensions):
            return ""
            
        parsed_url = urlparse(url)
        url_path = parsed_url.path
        if '.' in url_path:
            return Path(url_path).suffix
        return '.pdf'  # Default to PDF

    def _sanitize_filename(self, title: str, url: str) -> str:
        """Sanitizes filename and adds extension if needed."""
        safe_title = re.sub(r'[^\w\s\-\.]', '_', title)
        extension = self._determine_file_extension(url, safe_title)
        return safe_title + extension

    async def download_document(self, url: str, title: str, source: str):
        """Downloads a document with organized folder structure."""
        # Sanitize source for folder name
        source_name = self._sanitize_source_name(source)
        
        # Create source-specific folder
        source_dir = self.directories['documents'] / source_name
        source_dir.mkdir(exist_ok=True)
        
        # Sanitize filename
        safe_title = self._sanitize_filename(title, url)
        file_path = source_dir / safe_title

        if file_path.exists():
            self.logger.warning(f"Duplicate found, skipping: {safe_title}")
            self.duplicate_files.add(url)
            return

        try:
            async with self.session_semaphore:
                headers = {'Referer': BASE_URL}
                timeout = httpx.Timeout(120.0)
                async with httpx.AsyncClient(
                    timeout=timeout, 
                    headers=headers
                ) as client:
                    response = await client.get(url)
                    response.raise_for_status()

                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(response.content)
                
                self.logger.info(f"✅ Downloaded: {source_name}/{safe_title}")
                self.downloaded_files.add(url)
        except Exception as e:
            self.logger.error(f"❌ Failed to download {url}: {e}")
            self.failed_downloads.append((url, str(e)))

    def _sanitize_url_for_filename(self, url: str) -> str:
        """Sanitizes URL for use as filename."""
        url_name = urlparse(url).path.strip('/').replace('/', '_')
        return url_name if url_name else "root"

    def _is_category_page(self, url: str) -> bool:
        """Checks if URL is a category page that should be scraped."""
        return (
            '/termekeink/' in url and 
            url != "https://www.leier.hu/hu/termekeink"
        )

    async def _save_page_html(self, html: str, url: str):
        """Saves page HTML for debugging purposes."""
        url_name = self._sanitize_url_for_filename(url)
        page_file = self.directories['page_samples'] / f"{url_name}.html"
        async with aiofiles.open(
            page_file, 'w', encoding='utf-8'
        ) as f:
            await f.write(html)

    async def _scrape_product_pages(self, html: str, url: str):
        """Scrapes product pages from category pages."""
        if not self._is_category_page(url):
            return
            
        product_links = self.extract_product_links(html, url)
        # Limit to first 5 products for testing
        for product_url in product_links[:5]:
            await self.scrape_url(product_url)
            await asyncio.sleep(0.5)  # Rate limiting

    async def scrape_url(self, url: str):
        """Scrapes a specific URL for downloadable content."""
        if url in self.processed_urls:
            return

        self.logger.info(f"--- Scraping URL: {url} ---")
        html = await self.fetch_page(url)
        if not html:
            return

        # Save page HTML for debugging
        await self._save_page_html(html, url)

        # Extract documents from this page
        documents = self.extract_documents_from_html(html, url)
        for doc_url, doc_title in documents:
            self.discovered_docs.add((doc_url, doc_title, url))

        # If this is a category page, also scrape product pages
        await self._scrape_product_pages(html, url)

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
            doc_count = len(self.discovered_docs)
            self.logger.info(f"--- Downloading {doc_count} documents ---")
            tasks = [
                self.download_document(url, title, source) 
                for url, title, source in self.discovered_docs
            ]
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