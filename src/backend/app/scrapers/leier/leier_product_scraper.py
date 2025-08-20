#!/usr/bin/env python3
"""
LEIER Product-Specific Documents Scraper - Enhanced Version
==========================================================

This scraper targets individual LEIER product pages to extract and download
product-specific documents, technical data sheets, and related PDFs.

**Key Features:**
- **Product Page Scraping**: Extracts documents from individual product pages
- **Category Discovery**: Finds all products from category pages
- **Direct File Downloads**: Downloads from uploads/files/ directory
- **Comprehensive Coverage**: Handles multiple URL patterns
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
MAIN_PRODUCTS_URL = "https://www.leier.hu/hu/termekeink"


class LeierProductScraper:
    """Scrapes LEIER product pages for product-specific documents."""

    def __init__(self, test_mode: bool = False, max_concurrent: int = 5):
        self.test_mode = test_mode
        self.session_semaphore = asyncio.Semaphore(max_concurrent)
        
        # Setup paths
        current_dir = Path(__file__).resolve()
        project_root = current_dir.parents[3]
        self.base_dir = project_root / "src" / "downloads" / "leier_product_docs"
        self.reports_dir = project_root / "leier_scraping_reports"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Storage directories
        self.directories = {
            'documents': self.base_dir / 'documents',
            'duplicates': self.base_dir / 'duplicates',
            'product_pages': self.base_dir / 'product_pages'
        }
        for directory in self.directories.values():
            directory.mkdir(parents=True, exist_ok=True)

        # Tracking
        self.discovered_products: Set[Tuple[str, str]] = set()  # (url, name)
        self.discovered_docs: Set[Tuple[str, str, str]] = set()  # (url, title, product)
        self.downloaded_files: Set[str] = set()
        self.failed_downloads: List[Tuple[str, str]] = []
        self.duplicate_files: Set[str] = set()
        self.processed_categories: Set[str] = set()

        self.setup_logging()

    def setup_logging(self):
        """Sets up logging for the scraper."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.reports_dir / f'leier_product_scraper_{timestamp}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("🚀 LEIER Product Scraper (Enhanced) Initialized")

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

    def _get_product_link_selectors(self) -> List[str]:
        """Returns CSS selectors for finding product links."""
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

    def _extract_product_name(self, link) -> str:
        """Extracts product name from a link element."""
        name = link.get_text(strip=True) or link.get('title', '')
        if not name:
            # Try to get name from image alt text
            img = link.find('img')
            if img:
                name = img.get('alt', '')
        return name

    def _is_duplicate_product(self, full_url: str, products: List[Tuple[str, str]]) -> bool:
        """Checks if a product URL is already in the products list."""
        return full_url in [p[0] for p in products]

    def extract_product_urls_from_category(self, html: str, category_url: str) -> List[Tuple[str, str]]:
        """Extracts product URLs from a category page."""
        soup = BeautifulSoup(html, 'html.parser')
        products = []

        selectors = self._get_product_link_selectors()
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href', '')
                if not self._is_valid_product_link(href):
                    continue
                    
                full_url = urljoin(BASE_URL, href)
                name = self._extract_product_name(link)
                
                if name and not self._is_duplicate_product(full_url, products):
                    products.append((full_url, name))

        self.logger.info(f"Found {len(products)} products in category: {category_url}")
        return products

    def _get_category_link_selectors(self) -> List[str]:
        """Returns CSS selectors for finding category links."""
        return [
            'a[href*="/termekeink/"]',  # Category links
            'a[href*="/hu/termekeink/"]',  # Full category links
            '.category-item a',  # Category containers
            'div[class*="category"] a'  # Category div containers
        ]

    def _is_valid_category_link(self, href: str) -> bool:
        """Checks if a link is a valid category link."""
        return href and '/termekeink/' in href and href != MAIN_PRODUCTS_URL

    def _extract_category_name(self, link) -> str:
        """Extracts category name from a link element."""
        return link.get_text(strip=True) or link.get('title', '')

    def _is_duplicate_category(self, full_url: str, categories: List[Tuple[str, str]]) -> bool:
        """Checks if a category URL is already in the categories list."""
        return full_url in [c[0] for c in categories]

    def extract_category_urls_from_main(self, html: str) -> List[Tuple[str, str]]:
        """Extracts category URLs from the main products page."""
        soup = BeautifulSoup(html, 'html.parser')
        categories = []

        selectors = self._get_category_link_selectors()
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href', '')
                if not self._is_valid_category_link(href):
                    continue
                    
                full_url = urljoin(BASE_URL, href)
                name = self._extract_category_name(link)
                
                if name and not self._is_duplicate_category(full_url, categories):
                    categories.append((full_url, name))

        self.logger.info(f"Found {len(categories)} categories in main page")
        return categories

    def _get_document_link_selectors(self) -> List[str]:
        """Returns CSS selectors for finding document links."""
        return [
            'a[href$=".pdf"]',  # Direct PDF links
            'a[href*=".pdf"]',  # PDF links with parameters
            'a[href*="/uploads/files/"]',  # File server links
            'a[href*="dokumentumtar"]',  # Document archive links
            '.document-link a',  # Document containers
            '.related-documents a',  # Related documents section
            'div[class*="document"] a'  # Document div containers
        ]

    def _is_valid_document_link(self, href: str) -> bool:
        """Checks if a link is a valid document link."""
        return href and ('.pdf' in href.lower() or '/uploads/files/' in href)

    def _extract_document_title(self, link, href: str) -> str:
        """Extracts document title from a link element."""
        title = link.get_text(strip=True) or link.get('title', '')
        if not title:
            # Try to extract from href
            title = Path(urlparse(href).path).stem
        return title

    def _is_duplicate_document(self, full_url: str, documents: List[Tuple[str, str]]) -> bool:
        """Checks if a document URL is already in the documents list."""
        return full_url in [d[0] for d in documents]

    def _extract_documents_from_html_selectors(self, soup: BeautifulSoup) -> List[Tuple[str, str]]:
        """Extracts documents using CSS selectors."""
        documents = []
        selectors = self._get_document_link_selectors()
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href', '')
                if not self._is_valid_document_link(href):
                    continue
                    
                full_url = urljoin(BASE_URL, href)
                title = self._extract_document_title(link, href)
                
                if title and not self._is_duplicate_document(full_url, documents):
                    documents.append((full_url, title))
        
        return documents

    def _extract_documents_from_scripts(self, soup: BeautifulSoup) -> List[Tuple[str, str]]:
        """Extracts documents from JavaScript in script tags."""
        documents = []
        scripts = soup.find_all('script')
        
        for script in scripts:
            if script.string:
                # Look for PDF URLs in JavaScript
                pdf_matches = re.findall(r'["\']([^"\']*\.pdf[^"\']*)["\']', script.string)
                for match in pdf_matches:
                    full_url = urljoin(BASE_URL, match)
                    title = Path(urlparse(match).path).stem
                    
                    if not self._is_duplicate_document(full_url, documents):
                        documents.append((full_url, title))
        
        return documents

    def extract_documents_from_product(self, html: str, product_url: str, product_name: str) -> List[Tuple[str, str]]:
        """Extracts document URLs from a product page."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract documents from HTML selectors
        html_documents = self._extract_documents_from_html_selectors(soup)
        
        # Extract documents from JavaScript
        script_documents = self._extract_documents_from_scripts(soup)
        
        # Combine all documents
        all_documents = html_documents + script_documents
        
        # Remove duplicates while preserving order
        unique_documents = []
        seen_urls = set()
        for url, title in all_documents:
            if url not in seen_urls:
                unique_documents.append((url, title))
                seen_urls.add(url)

        self.logger.info(f"Found {len(unique_documents)} documents in product: {product_name}")
        return unique_documents

    def _sanitize_product_name(self, product_name: str) -> str:
        """Sanitizes product name for use as folder name."""
        safe_product = re.sub(r'[^\w\s\-]', '_', product_name)
        return re.sub(r'\s+', '_', safe_product)

    def _sanitize_document_title(self, title: str) -> str:
        """Sanitizes document title for use as filename."""
        safe_title = re.sub(r'[^\w\s\-\.]', '_', title)
        if not safe_title.lower().endswith('.pdf'):
            safe_title += '.pdf'
        return safe_title

    def _is_duplicate_file(self, file_path: Path) -> bool:
        """Checks if a file already exists."""
        return file_path.exists()

    async def download_document(self, url: str, title: str, product_name: str):
        """Downloads a document with organized folder structure."""
        # Sanitize names
        safe_product = self._sanitize_product_name(product_name)
        safe_title = self._sanitize_document_title(title)
        
        # Create product-specific folder
        product_dir = self.directories['documents'] / safe_product
        product_dir.mkdir(exist_ok=True)
        
        file_path = product_dir / safe_title

        if self._is_duplicate_file(file_path):
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
                
                self.logger.info(f"✅ Downloaded: {product_name}/{safe_title}")
                self.downloaded_files.add(url)
        except Exception as e:
            self.logger.error(f"❌ Failed to download {url}: {e}")
            self.failed_downloads.append((url, str(e)))

    def _is_category_processed(self, category_url: str) -> bool:
        """Checks if a category has already been processed."""
        return category_url in self.processed_categories

    async def _save_product_page(self, html: str, product_name: str):
        """Saves product page HTML for debugging."""
        safe_name = re.sub(r'[^\w\s\-]', '_', product_name)
        page_file = self.directories['product_pages'] / f"{safe_name}.html"
        async with aiofiles.open(page_file, 'w', encoding='utf-8') as f:
            await f.write(html)

    async def scrape_category(self, category_url: str, category_name: str):
        """Scrapes all products from a category."""
        if self._is_category_processed(category_url):
            return

        self.logger.info(f"--- Scraping category: {category_name} ---")
        html = await self.fetch_page(category_url)
        if not html:
            return

        # Extract products from category
        products = self.extract_product_urls_from_category(html, category_url)
        
        for product_url, product_name in products:
            self.discovered_products.add((product_url, product_name))
            
            # Scrape individual product
            await self.scrape_product(product_url, product_name)
            
            # Rate limiting
            await asyncio.sleep(0.5)

        self.processed_categories.add(category_url)

    async def scrape_product(self, product_url: str, product_name: str):
        """Scrapes documents from an individual product page."""
        self.logger.info(f"Scraping product: {product_name}")
        html = await self.fetch_page(product_url)
        if not html:
            return

        # Save product page HTML for debugging
        await self._save_product_page(html, product_name)

        # Extract documents from product page
        documents = self.extract_documents_from_product(html, product_url, product_name)
        
        for doc_url, doc_title in documents:
            self.discovered_docs.add((doc_url, doc_title, product_name))

    def _should_skip_downloads(self) -> bool:
        """Determines if downloads should be skipped."""
        return self.test_mode

    def _has_documents_to_download(self) -> bool:
        """Checks if there are documents to download."""
        return bool(self.discovered_docs)

    async def _download_all_documents(self):
        """Downloads all discovered documents."""
        doc_count = len(self.discovered_docs)
        self.logger.info(f"--- Downloading {doc_count} documents ---")
        
        tasks = [
            self.download_document(url, title, product) 
            for url, title, product in self.discovered_docs
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def run(self):
        """Main execution logic for the product scraper."""
        start_time = datetime.now()
        self.logger.info("--- Starting LEIER Product Document Scraping ---")

        # Step 1: Get main products page
        main_html = await self.fetch_page(MAIN_PRODUCTS_URL)
        if not main_html:
            self.logger.error("Failed to fetch main products page")
            return

        # Step 2: Extract categories
        categories = self.extract_category_urls_from_main(main_html)
        self.logger.info(f"Found {len(categories)} categories to process")

        # Step 3: Process each category
        for category_url, category_name in categories:
            await self.scrape_category(category_url, category_name)

        # Step 4: Download all discovered documents
        if self._should_skip_downloads():
            self.logger.info("Test mode enabled. Skipping downloads.")
        elif self._has_documents_to_download():
            await self._download_all_documents()
        else:
            self.logger.warning("No documents discovered to download.")

        self.generate_report(start_time)

    def generate_report(self, start_time: datetime):
        """Generates and saves a JSON report of the scraping run."""
        report = {
            "run_timestamp": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "test_mode": self.test_mode,
            "target_url": MAIN_PRODUCTS_URL,
            "summary": {
                "categories_processed": len(self.processed_categories),
                "products_discovered": len(self.discovered_products),
                "documents_discovered": len(self.discovered_docs),
                "downloads_successful": len(self.downloaded_files),
                "downloads_failed": len(self.failed_downloads),
                "duplicates_found": len(self.duplicate_files),
            },
            "discovered_products_sample": [
                {"url": url, "name": name} 
                for url, name in list(self.discovered_products)[:10]
            ],
            "discovered_docs_sample": [
                {"url": url, "title": title, "product": product} 
                for url, title, product in list(self.discovered_docs)[:20]
            ],
            "failed_downloads": self.failed_downloads,
        }
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'leier_product_scraping_report_{timestamp}.json'
        report_path = self.reports_dir / filename
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
        self.logger.info(f"📊 Report saved to {report_path}")


async def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="LEIER Product-Specific Documents Scraper"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (discover links but do not download).",
    )
    args = parser.parse_args()

    scraper = LeierProductScraper(test_mode=args.test)
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main()) 