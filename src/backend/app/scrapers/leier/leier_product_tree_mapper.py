#!/usr/bin/env python3
"""
LEIER Complete Product Tree Mapper
==================================

This scraper creates a comprehensive mapping of the LEIER product tree from:
https://www.leier.hu/hu/termekeink/

Features:
- Complete product hierarchy mapping (26+ categories)
- Individual product information extraction
- Product-specific document collection
- Organized directory structure per product
- JSON metadata for each product
- PDF document storage with product separation
"""

import asyncio
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any
from urllib.parse import urljoin, urlparse

import aiofiles
import httpx
from bs4 import BeautifulSoup

# --- Configuration ---
BASE_URL = "https://www.leier.hu"
MAIN_PRODUCTS_URL = "https://www.leier.hu/hu/termekeink"

class LeierProductTreeMapper:
    """Maps complete LEIER product tree with documents and metadata."""

    def __init__(self, max_concurrent: int = 3):
        self.session_semaphore = asyncio.Semaphore(max_concurrent)
        
        # Setup paths
        current_dir = Path(__file__).resolve()
        project_root = current_dir.parents[3]
        self.base_dir = project_root / "src" / "downloads" / "leier_products_complete"
        self.reports_dir = project_root / "leier_scraping_reports"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Storage directories
        self.directories = {
            'products': self.base_dir / 'products',
            'categories': self.base_dir / 'categories',
            'tree_mapping': self.base_dir / 'tree_mapping',
            'documents': self.base_dir / 'documents'
        }
        for directory in self.directories.values():
            directory.mkdir(parents=True, exist_ok=True)

        # Data structures
        self.product_tree: Dict[str, Any] = {
            "website": "https://www.leier.hu",
            "main_page": MAIN_PRODUCTS_URL,
            "scrape_timestamp": datetime.now().isoformat(),
            "categories": {},
            "total_categories": 0,
            "total_products": 0,
            "total_documents": 0
        }
        
        self.discovered_categories: Dict[str, Dict[str, Any]] = {}
        self.discovered_products: Dict[str, Dict[str, Any]] = {}
        self.discovered_documents: Dict[str, Dict[str, Any]] = {}
        self.failed_operations: List[Tuple[str, str, str]] = []

        self.setup_logging()

    def setup_logging(self):
        """Sets up logging for the scraper."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.reports_dir / f'leier_product_tree_mapper_{timestamp}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("🚀 LEIER Product Tree Mapper Initialized")

    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetches HTML content from a URL."""
        try:
            async with self.session_semaphore:
                timeout = httpx.Timeout(45.0)
                headers = {
                    'User-Agent': (
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36'
                    ),
                    'Accept': (
                        'text/html,application/xhtml+xml,application/xml;'
                        'q=0.9,*/*;q=0.8'
                    )
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
            self.failed_operations.append(("fetch_page", url, str(e)))
            return None

    def _get_category_link_selectors(self) -> List[str]:
        """Returns CSS selectors for finding category links."""
        return [
            'a[href*="/termekeink/"]',
            'a[href*="/hu/termekeink/"]',
        ]

    def _is_valid_category_link(self, href: str) -> bool:
        """Checks if an href is a valid, non-root category link."""
        return href and '/termekeink/' in href and href != MAIN_PRODUCTS_URL

    def _extract_category_info_from_link(self, link) -> Dict[str, Any]:
        """Extracts category information from a single BeautifulSoup link tag."""
        href = link.get('href', '')
        full_url = urljoin(BASE_URL, href)
        name = link.get_text(strip=True)
        
        description = ""
        parent = link.find_parent()
        if parent:
            desc_text = parent.get_text(strip=True)
            if desc_text and desc_text != name:
                description = desc_text
        
        category_id = href.split('/')[-1] if '/' in href else href
        
        return {
            "category_id": category_id,
            "name": name,
            "description": description,
            "url": full_url,
            "products": {},
            "product_count": 0,
            "document_count": 0
        }

    def extract_categories_from_main_page(self, html: str) -> List[Dict[str, Any]]:
        """Extracts all product categories from the main products page."""
        soup = BeautifulSoup(html, 'html.parser')
        categories = []
        seen_urls = set()
        
        selectors = self._get_category_link_selectors()
        for selector in selectors:
            for link in soup.select(selector):
                href = link.get('href', '')
                if not self._is_valid_category_link(href):
                    continue
                
                category_info = self._extract_category_info_from_link(link)
                if category_info['url'] not in seen_urls:
                    categories.append(category_info)
                    seen_urls.add(category_info['url'])

        self.logger.info(f"Found {len(categories)} categories in main page")
        return categories

    def _get_product_link_selectors(self) -> List[str]:
        """Returns CSS selectors for finding product links."""
        return [
            'a[href*="/termekek/"]',
            'a[href*="/hu/termekek/"]',
        ]

    def _is_valid_product_link(self, href: str) -> bool:
        """Checks if an href is a valid product link."""
        return href and '/termekek/' in href

    def _extract_product_info_from_link(
        self, link: Any, category_url: str
    ) -> Dict[str, Any]:
        """Extracts product information from a single BeautifulSoup link tag."""
        href = link.get('href', '')
        full_url = urljoin(BASE_URL, href)
        name = link.get_text(strip=True)
        
        description = ""
        parent = link.find_parent()
        if parent:
            desc_elements = parent.find_all(['p', 'div', 'span'])
            for elem in desc_elements:
                text = elem.get_text(strip=True)
                if text and text != name and len(text) > 20:
                    description = text[:200] + "..." if len(text) > 200 else text
                    break

        product_id = href.split('/')[-1] if '/' in href else href
        
        return {
            "product_id": product_id,
            "name": name,
            "description": description,
            "url": full_url,
            "category_url": category_url,
            "price_info": "",
            "specifications": {},
            "documents": {},
            "document_count": 0,
            "images": []
        }

    def extract_products_from_category(
        self, html: str, category_url: str
    ) -> List[Dict[str, Any]]:
        """Extracts all products from a category page."""
        soup = BeautifulSoup(html, 'html.parser')
        products = []
        seen_urls = set()

        selectors = self._get_product_link_selectors()
        for selector in selectors:
            for link in soup.select(selector):
                href = link.get('href', '')
                if not self._is_valid_product_link(href):
                    continue

                product_info = self._extract_product_info_from_link(link, category_url)
                if product_info['url'] not in seen_urls:
                    products.append(product_info)
                    seen_urls.add(product_info['url'])
        return products

    def _extract_description_from_details(self, soup: BeautifulSoup) -> str:
        """Extracts the main product description from the details page."""
        selectors = [
            '.product-description', '.description', 
            '[class*="description"]', 'p'
        ]
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if len(text) > 50:
                    return text
        return ""

    def _extract_tech_data_from_details(
        self, soup: BeautifulSoup
    ) -> Dict[str, str]:
        """Extracts technical data from tables on the details page."""
        tech_data = {}
        tables = soup.find_all('table')
        for table in tables:
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    if key and value:
                        tech_data[key] = value
        return tech_data

    def _extract_features_from_details(
        self, soup: BeautifulSoup
    ) -> List[str]:
        """Extracts product features from lists on the details page."""
        features = []
        selectors = [
            '.features li', '.characteristics li', 
            '[class*="feature"] li', 'ul li'
        ]
        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements[:10]:
                text = elem.get_text(strip=True)
                if text and len(text) > 10:
                    features.append(text)
        return features

    def _extract_documents_from_details(
        self, soup: BeautifulSoup
    ) -> Dict[str, Dict[str, str]]:
        """Extracts document links from the details page."""
        documents = {}
        selectors = [
            'a[href$=".pdf"]', 'a[href*=".pdf"]', 
            'a[href*="/uploads/files/"]', 'a[href*="dokumentumtar"]'
        ]
        for selector in selectors:
            for link in soup.select(selector):
                href = link.get('href', '')
                if not href:
                    continue
                
                full_url = urljoin(BASE_URL, href)
                title = (
                    link.get_text(strip=True) or 
                    link.get('title', '') or 
                    Path(urlparse(href).path).stem
                )
                doc_id = f"doc_{len(documents)}"
                doc_type = "pdf" if ".pdf" in href.lower() else "document"
                documents[doc_id] = {
                    "title": title, "url": full_url, "type": doc_type
                }
        return documents

    def _extract_images_from_details(
        self, soup: BeautifulSoup
    ) -> List[Dict[str, str]]:
        """Extracts image URLs from the details page."""
        images = []
        selectors = [
            '.product-image img', '.gallery img', 
            'img[src*="product"]', 'img'
        ]
        for selector in selectors:
            for img in soup.select(selector)[:5]:
                src = img.get('src', '')
                if src:
                    full_url = urljoin(BASE_URL, src)
                    alt_text = img.get('alt', '')
                    images.append({"url": full_url, "alt": alt_text})
        return images

    def extract_product_details(
        self, html: str, product_url: str
    ) -> Dict[str, Any]:
        """Extracts detailed information from a product page."""
        soup = BeautifulSoup(html, 'html.parser')
        
        return {
            "description": self._extract_description_from_details(soup),
            "technical_data": self._extract_tech_data_from_details(soup),
            "features": self._extract_features_from_details(soup),
            "documents": self._extract_documents_from_details(soup),
            "images": self._extract_images_from_details(soup),
            "specifications": {}, # backward compatibility
        }

    async def download_document(
        self, doc_info: Dict[str, str], product_id: str, category_id: str
    ):
        """Downloads a document to the organized directory structure."""
        doc_url = doc_info["url"]
        doc_title = doc_info["title"]
        
        # Create organized directory structure
        category_dir = self.directories['documents'] / category_id
        product_dir = category_dir / product_id
        product_dir.mkdir(parents=True, exist_ok=True)
        
        # Sanitize filename
        safe_title = re.sub(r'[^\w\s\-\.]', '_', doc_title)
        if not safe_title.lower().endswith('.pdf'):
            safe_title += '.pdf'
        
        file_path = product_dir / safe_title

        if file_path.exists():
            self.logger.warning(
                f"Document already exists: {category_id}/{product_id}/{safe_title}"
            )
            return file_path

        try:
            async with self.session_semaphore:
                headers = {'Referer': BASE_URL}
                timeout = httpx.Timeout(120.0)
                async with httpx.AsyncClient(
                    timeout=timeout, headers=headers
                ) as client:
                    response = await client.get(doc_url)
                    response.raise_for_status()

                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(response.content)
                
                file_size = file_path.stat().st_size / 1024  # KB
                self.logger.info(
                    f"✅ Downloaded: {category_id}/{product_id}/"
                    f"{safe_title} ({file_size:.1f} KB)"
                )
                return file_path
                
        except Exception as e:
            self.logger.error(f"❌ Failed to download {doc_url}: {e}")
            self.failed_operations.append(("download_document", doc_url, str(e)))
            return None

    async def save_product_metadata(
        self, product_info: Dict[str, Any], category_id: str
    ):
        """Saves product metadata as JSON."""
        product_id = product_info["product_id"]
        
        # Create directory structure
        category_dir = self.directories['products'] / category_id
        category_dir.mkdir(parents=True, exist_ok=True)
        
        # Save product metadata
        metadata_file = category_dir / f"{product_id}.json"
        async with aiofiles.open(metadata_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(product_info, indent=4, ensure_ascii=False))
        
        self.logger.info(
            f"💾 Saved metadata: {category_id}/{product_id}.json"
        )

    async def process_product(
        self, product_info: Dict[str, Any], category_id: str
    ):
        """Processes a single product: extracts details and downloads documents."""
        product_url = product_info["url"]
        product_id = product_info["product_id"]
        
        self.logger.info(f"Processing product: {product_info['name']}")
        
        # Fetch product page
        html = await self.fetch_page(product_url)
        if not html:
            return
        
        # Extract detailed product information
        details = self.extract_product_details(html, product_url)
        
        # Merge details into product info
        product_info.update(details)
        product_info["document_count"] = len(details["documents"])
        
        # Save product metadata
        await self.save_product_metadata(product_info, category_id)
        
        # Download all product documents
        if "documents" in details and details["documents"]:
            for doc_id, doc_info in details["documents"].items():
                await self.download_document(doc_info, product_id, category_id)
                await asyncio.sleep(0.5)  # Rate limiting

    async def process_category(self, category_info: Dict[str, Any]):
        """Processes a single category: finds products and processes them."""
        category_url = category_info["url"]
        category_id = category_info["category_id"]
        
        self.logger.info(f"--- Processing category: {category_info['name']} ---")
        
        # Fetch category page
        html = await self.fetch_page(category_url)
        if not html:
            return
        
        # Extract products from category
        products = self.extract_products_from_category(html, category_url)
        self.logger.info(f"Found {len(products)} products in category: {category_info['name']}")
        
        # Update category info
        category_info["product_count"] = len(products)
        category_info["products"] = {prod["product_id"]: prod for prod in products}
        
        # Process each product
        for product_info in products:
            await self.process_product(product_info, category_id)
            await asyncio.sleep(1)  # Rate limiting between products
        
        # Calculate total documents in category
        total_docs = sum(
            prod.get("document_count", 0) for prod in products
        )
        category_info["document_count"] = total_docs
        
        # Save category metadata
        category_file = self.directories['categories'] / f"{category_id}.json"
        async with aiofiles.open(category_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(category_info, indent=4, ensure_ascii=False))

    async def run(self):
        """Main execution logic for the product tree mapper."""
        start_time = datetime.now()
        self.logger.info("--- Starting LEIER Complete Product Tree Mapping ---")

        # Step 1: Get main products page
        main_html = await self.fetch_page(MAIN_PRODUCTS_URL)
        if not main_html:
            self.logger.error("Failed to fetch main products page")
            return

        # Step 2: Extract all categories
        categories = self.extract_categories_from_main_page(main_html)
        self.logger.info(f"Found {len(categories)} categories to process")
        
        self.product_tree["total_categories"] = len(categories)

        # Step 3: Process each category
        for category_info in categories:
            await self.process_category(category_info)
            
            # Update product tree
            cat_id = category_info["category_id"]
            self.product_tree["categories"][cat_id] = category_info
            
            await asyncio.sleep(2)  # Rate limiting between categories

        # Step 4: Calculate totals and generate final report
        total_products = sum(cat["product_count"] for cat in self.product_tree["categories"].values())
        total_documents = sum(cat["document_count"] for cat in self.product_tree["categories"].values())
        
        self.product_tree["total_products"] = total_products
        self.product_tree["total_documents"] = total_documents
        self.product_tree["processing_completed"] = datetime.now().isoformat()
        duration = (datetime.now() - start_time).total_seconds()
        self.product_tree["duration_seconds"] = duration

        # Save complete product tree
        tree_file = self.directories['tree_mapping'] / 'complete_product_tree.json'
        async with aiofiles.open(tree_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(self.product_tree, indent=2, ensure_ascii=False))

        self.generate_final_report(start_time)

    def generate_final_report(self, start_time: datetime):
        """Generates and saves a comprehensive final report."""
        report = {
            "run_timestamp": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "target_url": MAIN_PRODUCTS_URL,
            "summary": {
                "categories_processed": len(self.product_tree["categories"]),
                "total_products": self.product_tree["total_products"],
                "total_documents": self.product_tree["total_documents"],
                "failed_operations": len(self.failed_operations),
            },
            "categories_overview": [
                {
                    "category_id": cat_id,
                    "name": cat_info.get("name"),
                    "product_count": cat_info.get("product_count"),
                    "document_count": cat_info.get("document_count"),
                }
                for cat_id, cat_info in self.product_tree["categories"].items()
            ],
            "failed_operations_log": self.failed_operations,
            "storage_structure": {
                "base_directory": str(self.base_dir),
                "products_metadata": "products/{category_id}/{product_id}.json",
                "categories_metadata": "categories/{category_id}.json",
                "documents": "documents/{category_id}/{product_id}/*.pdf",
                "complete_tree": "tree_mapping/complete_product_tree.json"
            }
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'leier_product_tree_final_report_{timestamp}.json'
        report_path = self.reports_dir / filename
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        self.logger.info(f"📊 Final report saved to {report_path}")
        
        # Print summary
        print("\n" + "="*80)
        print("🎉 LEIER PRODUCT TREE MAPPING COMPLETED!")
        print("="*80)
        print(f"📁 Categories processed: {report['summary']['categories_processed']}")
        print(f"📦 Products mapped: {report['summary']['total_products']}")
        print(f"📄 Documents collected: {report['summary']['total_documents']}")
        print(f"⏱️  Total time: {report['duration_seconds']:.1f} seconds")
        print(f"💾 Base directory: {self.base_dir}")
        print("="*80)


async def main():
    """Main execution entry point."""
    scraper = LeierProductTreeMapper(max_concurrent=5)
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main()) 