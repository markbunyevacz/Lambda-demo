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
from typing import Dict, Set, Optional, Tuple, List
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
        self.product_tree = {
            "website": "https://www.leier.hu",
            "main_page": MAIN_PRODUCTS_URL,
            "scrape_timestamp": datetime.now().isoformat(),
            "categories": {},
            "total_categories": 0,
            "total_products": 0,
            "total_documents": 0
        }
        
        self.discovered_categories: Dict[str, Dict] = {}
        self.discovered_products: Dict[str, Dict] = {}
        self.discovered_documents: Dict[str, Dict] = {}
        self.failed_operations = []

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
            self.failed_operations.append(("fetch_page", url, str(e)))
            return None

    def extract_categories_from_main_page(self, html: str) -> List[Dict]:
        """Extracts all product categories from the main products page."""
        soup = BeautifulSoup(html, 'html.parser')
        categories = []

        # Look for category links with various selectors
        selectors = [
            'a[href*="/termekeink/"]',  # Category links
            'a[href*="/hu/termekeink/"]',  # Full category links
        ]

        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href', '')
                if href and '/termekeink/' in href and href != MAIN_PRODUCTS_URL:
                    # Make absolute URL
                    full_url = urljoin(BASE_URL, href)
                    
                    # Extract category name and description
                    name = link.get_text(strip=True)
                    
                    # Try to find additional info from parent containers
                    parent = link.find_parent()
                    description = ""
                    if parent:
                        desc_text = parent.get_text(strip=True)
                        if desc_text and desc_text != name:
                            description = desc_text

                    # Extract category ID from URL
                    category_id = href.split('/')[-1] if '/' in href else href
                    
                    category_info = {
                        "category_id": category_id,
                        "name": name,
                        "description": description,
                        "url": full_url,
                        "products": {},
                        "product_count": 0,
                        "document_count": 0
                    }
                    
                    # Avoid duplicates
                    if not any(cat["url"] == full_url for cat in categories):
                        categories.append(category_info)

        self.logger.info(f"Found {len(categories)} categories in main page")
        return categories

    def extract_products_from_category(self, html: str, category_url: str) -> List[Dict]:
        """Extracts all products from a category page."""
        soup = BeautifulSoup(html, 'html.parser')
        products = []

        # Look for product links
        selectors = [
            'a[href*="/termekek/"]',  # Direct product links
            'a[href*="/hu/termekek/"]',  # Full product links
        ]

        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href', '')
                if href and '/termekek/' in href:
                    # Make absolute URL
                    full_url = urljoin(BASE_URL, href)
                    
                    # Extract product name
                    name = link.get_text(strip=True)
                    
                    # Try to get additional info from surrounding elements
                    parent = link.find_parent()
                    description = ""
                    price_info = ""
                    
                    if parent:
                        # Look for description
                        desc_elements = parent.find_all(['p', 'div', 'span'])
                        for elem in desc_elements:
                            text = elem.get_text(strip=True)
                            if text and text != name and len(text) > 20:
                                description = text[:200] + "..." if len(text) > 200 else text
                                break
                    
                    # Extract product ID from URL
                    product_id = href.split('/')[-1] if '/' in href else href
                    
                    product_info = {
                        "product_id": product_id,
                        "name": name,
                        "description": description,
                        "url": full_url,
                        "category_url": category_url,
                        "price_info": price_info,
                        "specifications": {},
                        "documents": {},
                        "document_count": 0,
                        "images": []
                    }
                    
                    # Avoid duplicates
                    if not any(prod["url"] == full_url for prod in products):
                        products.append(product_info)

        return products

    def extract_product_details(self, html: str, product_url: str) -> Dict:
        """Extracts detailed information from a product page."""
        soup = BeautifulSoup(html, 'html.parser')
        
        details = {
            "specifications": {},
            "documents": {},
            "images": [],
            "technical_data": {},
            "description": "",
            "features": []
        }

        # Extract product description
        desc_selectors = [
            '.product-description',
            '.description',
            '[class*="description"]',
            'p'
        ]
        
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                desc_text = desc_elem.get_text(strip=True)
                if len(desc_text) > 50:
                    details["description"] = desc_text
                    break

        # Extract technical specifications
        # Look for tables with technical data
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    if key and value:
                        details["technical_data"][key] = value

        # Extract features/characteristics
        feature_selectors = [
            '.features li',
            '.characteristics li',
            '[class*="feature"] li',
            'ul li'
        ]
        
        for selector in feature_selectors:
            feature_elements = soup.select(selector)
            for elem in feature_elements[:10]:  # Limit to first 10
                feature_text = elem.get_text(strip=True)
                if feature_text and len(feature_text) > 10:
                    details["features"].append(feature_text)

        # Extract document links
        doc_selectors = [
            'a[href$=".pdf"]',
            'a[href*=".pdf"]',
            'a[href*="/uploads/files/"]',
            'a[href*="dokumentumtar"]'
        ]

        for selector in doc_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href', '')
                if href:
                    full_url = urljoin(BASE_URL, href)
                    title = link.get_text(strip=True) or link.get('title', '')
                    if not title:
                        title = Path(urlparse(href).path).stem
                    
                    doc_id = f"doc_{len(details['documents'])}"
                    details["documents"][doc_id] = {
                        "title": title,
                        "url": full_url,
                        "type": "pdf" if ".pdf" in href.lower() else "document"
                    }

        # Extract product images
        img_selectors = [
            '.product-image img',
            '.gallery img',
            'img[src*="product"]',
            'img'
        ]
        
        for selector in img_selectors:
            images = soup.select(selector)
            for img in images[:5]:  # Limit to first 5 images
                src = img.get('src', '')
                if src:
                    full_url = urljoin(BASE_URL, src)
                    alt_text = img.get('alt', '')
                    details["images"].append({
                        "url": full_url,
                        "alt": alt_text
                    })

        return details

    async def download_document(self, doc_info: Dict, product_id: str, category_id: str):
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
            self.logger.warning(f"Document already exists: {category_id}/{product_id}/{safe_title}")
            return file_path

        try:
            async with self.session_semaphore:
                headers = {'Referer': BASE_URL}
                timeout = httpx.Timeout(120.0)
                async with httpx.AsyncClient(timeout=timeout, 
                                           headers=headers) as client:
                    response = await client.get(doc_url)
                    response.raise_for_status()

                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(response.content)
                
                file_size = file_path.stat().st_size / 1024  # KB
                self.logger.info(f"✅ Downloaded: {category_id}/{product_id}/{safe_title} ({file_size:.1f} KB)")
                return file_path
                
        except Exception as e:
            self.logger.error(f"❌ Failed to download {doc_url}: {e}")
            self.failed_operations.append(("download_document", doc_url, str(e)))
            return None

    async def save_product_metadata(self, product_info: Dict, category_id: str):
        """Saves product metadata as JSON."""
        product_id = product_info["product_id"]
        
        # Create directory structure
        category_dir = self.directories['products'] / category_id
        category_dir.mkdir(parents=True, exist_ok=True)
        
        # Save product metadata
        metadata_file = category_dir / f"{product_id}.json"
        async with aiofiles.open(metadata_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(product_info, indent=4, ensure_ascii=False))
        
        self.logger.info(f"💾 Saved metadata: {category_id}/{product_id}.json")

    async def process_product(self, product_info: Dict, category_id: str):
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
        for doc_id, doc_info in details["documents"].items():
            await self.download_document(doc_info, product_id, category_id)
            await asyncio.sleep(0.5)  # Rate limiting

    async def process_category(self, category_info: Dict):
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
        total_docs = sum(prod["document_count"] for prod in products)
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
        self.product_tree["duration_seconds"] = (datetime.now() - start_time).total_seconds()

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
                    "name": cat_info["name"],
                    "product_count": cat_info["product_count"],
                    "document_count": cat_info["document_count"]
                }
                for cat_id, cat_info in self.product_tree["categories"].items()
            ],
            "failed_operations": self.failed_operations,
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
            json.dump(report, f, indent=4, ensure_ascii=False)
            
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
    """Main execution function."""
    scraper = LeierProductTreeMapper()
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main()) 