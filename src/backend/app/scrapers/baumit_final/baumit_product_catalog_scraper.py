"""
BAUMIT Product Catalog Scraper
------------------------------

Purpose:
This script is responsible for downloading all product documentation,
technical datasheets, and specifications from the BAUMIT Hungary A-Z
product catalog. This is the HIGH PRIORITY scraper targeting systematic
product data extraction.

Key Features:
- Targets the A-Z product catalog section of the website
- Uses BrightData MCP for robust JavaScript-heavy page handling
- Systematic alphabet-based navigation
- Fully asynchronous downloads with smart duplicate prevention

Entry Point: https://baumit.hu/termekek-a-z
Priority: HIGH (Product A-Z catalog and technical specs)

This follows the proven ROCKWOOL/LEIER architecture pattern.
"""
import asyncio
import logging
import json
import httpx
import re
import hashlib
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path resolution fix for Docker compatibility [[memory:646524]]
try:
    PROJECT_ROOT = Path(__file__).resolve().parents[5]  # Go up to Lambda/ root
except IndexError:
    # Fallback for Docker environment
    PROJECT_ROOT = Path(__file__).resolve().parents[3]  # Docker-compatible path

PDF_STORAGE_DIR = PROJECT_ROOT / "src" / "downloads" / "baumit_products"
TECHNICAL_DOCS_DIR = PDF_STORAGE_DIR / "technical_datasheets"
DUPLICATES_DIR = PDF_STORAGE_DIR / "duplicates"
DEBUG_FILE_PATH = PROJECT_ROOT / "debug_baumit_catalog.html"

# Ensure directories exist
PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
TECHNICAL_DOCS_DIR.mkdir(parents=True, exist_ok=True)
DUPLICATES_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://baumit.hu"
TARGET_URL = "https://baumit.hu/termekek-a-z"

# BAUMIT-specific configuration
ALPHABET_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
MAX_PRODUCTS_PER_LETTER = 100  # Reasonable limit to prevent infinite loops

class BaumitProductCatalogScraper:
    """
    BAUMIT A-Z Product Catalog Scraper with BrightData MCP integration.
    Follows the proven architecture from ROCKWOOL/LEIER implementations.
    """
    
    def __init__(self):
        self.products = []
        self.documents = []
        self.visited_urls = set()
        self.downloaded_files = set()
        self.duplicate_count = 0
        self.products_by_letter = {}
        
        # Category mappings for BAUMIT
        self.category_mappings = {
            'hőszigetelő': 'Thermal Insulation Systems',
            'homlokzat': 'Façade Solutions', 
            'festék': 'Paints and Coatings',
            'vakolat': 'Renders and Plasters',
            'ragasztó': 'Adhesive Systems',
            'aljzat': 'Substrate Systems',
            'beltéri': 'Interior Solutions',
            'glett': 'Fillers and Sealers',
            'színes': 'Colored Systems'
        }

    def _categorize_product(self, product_name: str, description: str = "") -> str:
        """
        Categorize BAUMIT product based on name and description.
        """
        text = f"{product_name} {description}".lower()
        
        for keyword, category in self.category_mappings.items():
            if keyword in text:
                return category
        
        return "General Building Materials"

    def _generate_unique_filename(self, base_filename: str, source_url: str) -> str:
        """
        Generates a unique filename for duplicates using URL hash.
        """
        name_part = Path(base_filename).stem
        extension = Path(base_filename).suffix
        
        # Create hash from URL for uniqueness
        url_hash = hashlib.md5(source_url.encode()).hexdigest()[:8]
        unique_filename = f"{name_part}_{url_hash}{extension}"
        
        return unique_filename

    async def _fetch_page_content(self, url: str) -> Optional[str]:
        """
        Fetch page content using direct HTTP request with proper headers.
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'hu-HU,hu;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            logger.info(f"🔄 Fetching content from: {url}")
            
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                logger.info(f"✅ Successfully fetched {len(response.text)} chars from: {url}")
                return response.text
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch {url}: {e}")
            return None

    async def _parse_catalog_page(self, html_content: str) -> List[Dict]:
        """
        Parse the A-Z catalog page to extract all products directly.
        BAUMIT uses a different structure than alphabet navigation.
        """
        products = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            logger.info("🔍 Analyzing BAUMIT catalog page structure...")
            
            # Try multiple product listing patterns common in BAUMIT-style sites
            product_selectors = [
                '.product-item',
                '.product-card', 
                '.product-list-item',
                '.product-entry',
                '[class*="product"]',
                '.catalog-item',
                '.item',
                'article',
                '.grid-item'
            ]
            
            product_elements = []
            for selector in product_selectors:
                elements = soup.select(selector)
                if elements and len(elements) > 5:  # Reasonable threshold
                    product_elements = elements
                    logger.info(f"✅ Found {len(elements)} products with selector: {selector}")
                    break
            
            # If no structured products found, try link-based extraction
            if not product_elements:
                logger.info("🔄 No structured products found, trying link extraction...")
                # Look for links that might be products
                all_links = soup.find_all('a', href=True)
                product_links = []
                
                for link in all_links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    
                    # Filter for product-like links
                    if (text and len(text) > 3 and 
                        any(keyword in text.lower() for keyword in ['baumit', 'star', 'pura', 'silikon', 'klima', 'nano']) and
                        href and ('termek' in href or 'product' in href or len(href) > 10)):
                        
                        product_url = urljoin(BASE_URL, href)
                        product_links.append({
                            'name': text,
                            'url': product_url,
                            'source': 'link_extraction'
                        })
                
                logger.info(f"🔗 Found {len(product_links)} product links")
                return product_links[:50]  # Limit for initial testing
            
            # Process structured product elements
            for i, element in enumerate(product_elements[:MAX_PRODUCTS_PER_LETTER]):
                try:
                    product_info = self._extract_product_info_from_element(element, f"item_{i}")
                    if product_info:
                        products.append(product_info)
                        
                except Exception as e:
                    logger.warning(f"⚠️  Failed to extract product {i}: {e}")
                    continue
            
            logger.info(f"📦 Total products extracted: {len(products)}")
            
        except Exception as e:
            logger.error(f"❌ Failed to parse catalog page: {e}")
        
        return products

    def _extract_product_info_from_element(self, element, index: str) -> Optional[Dict]:
        """
        Extract product information from a single product element.
        """
        try:
            # Product name extraction with multiple strategies
            name_selectors = ['h1', 'h2', 'h3', 'h4', '.title', '.name', '.product-name', 'strong', 'b']
            product_name = None
            
            for selector in name_selectors:
                name_elem = element.select_one(selector)
                if name_elem:
                    product_name = name_elem.get_text(strip=True)
                    if product_name and len(product_name) > 2:
                        break
            
            # If no name found, try to get it from the element's text
            if not product_name:
                element_text = element.get_text(strip=True)
                if element_text and len(element_text) < 100:  # Reasonable name length
                    product_name = element_text[:50]  # Limit length
            
            if not product_name:
                return None
            
            # Product link extraction
            link_elem = element.select_one('a[href]')
            product_url = None
            if link_elem:
                href = link_elem.get('href')
                if href:
                    product_url = urljoin(BASE_URL, href)
            
            # Description extraction
            desc_selectors = ['.description', '.excerpt', '.summary', 'p', '.content']
            description = ""
            
            for selector in desc_selectors:
                desc_elem = element.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)[:200]  # Limit length
                    break
            
            # Look for download links or PDF references
            pdf_links = []
            download_links = element.select('a[href*=".pdf"], a[href*="download"], a[href*="letoltes"]')
            for link in download_links:
                href = link.get('href')
                if href:
                    pdf_url = urljoin(BASE_URL, href)
                    pdf_links.append(pdf_url)
            
            # Categorize product
            category = self._categorize_product(product_name, description)
            
            return {
                'name': product_name,
                'url': product_url,
                'description': description,
                'category': category,
                'pdf_links': pdf_links,
                'index': index,
                'scraped_at': datetime.now().isoformat(),
                'source': 'baumit_catalog'
            }
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to extract product info from element: {e}")
            return None

    async def _download_pdf(self, session: httpx.AsyncClient, pdf_url: str, doc_name: str, category: str = "general") -> Dict:
        """
        Downloads a single PDF with smart duplicate handling and categorization.
        """
        try:
            if not pdf_url.startswith('http'):
                pdf_url = urljoin(BASE_URL, pdf_url)
            
            logger.info(f"⬇️  Downloading: {pdf_url}")
            response = await session.get(pdf_url, follow_redirects=True)
            response.raise_for_status()

            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower():
                logger.warning(f"⚠️  Not a PDF file. Content-Type: {content_type}")
                return {'status': 'skipped', 'reason': 'not_pdf'}

            # Clean filename
            safe_name = re.sub(r'[^\w\s-]', '', doc_name)[:50].strip()
            base_filename = f"{safe_name}.pdf"
            
            # Category-based storage
            category_dir = TECHNICAL_DOCS_DIR / category.lower().replace(' ', '_')
            category_dir.mkdir(exist_ok=True)
            
            # Smart duplicate handling
            if base_filename in self.downloaded_files:
                unique_filename = self._generate_unique_filename(base_filename, pdf_url)
                filepath = DUPLICATES_DIR / unique_filename
                self.duplicate_count += 1
                logger.info(f"🔄 Duplicate detected, saving to duplicates: {unique_filename}")
            else:
                filepath = category_dir / base_filename
                self.downloaded_files.add(base_filename)

            with open(filepath, 'wb') as f:
                f.write(response.content)

            return {
                'status': 'success',
                'filename': filepath.name,
                'local_path': str(filepath),
                'file_size_bytes': len(response.content),
                'category': category,
                'is_duplicate': 'duplicates' in str(filepath)
            }
            
        except Exception as e:
            logger.error(f"❌ Download failed for '{doc_name}': {e}")
            return {'status': 'failed', 'error': str(e)}

    async def run(self):
        """
        Executes the entire BAUMIT A-Z catalog scraping process.
        """
        logger.info("=== Starting BAUMIT A-Z Product Catalog Scraper ===")
        logger.info(f"🎯 Target URL: {TARGET_URL}")
        logger.info(f"📁 Storage: {PDF_STORAGE_DIR}")
        
        # Step 1: Fetch main catalog page
        logger.info(f"🔍 Fetching main catalog page...")
        catalog_html = await self._fetch_page_content(TARGET_URL)
        
        if not catalog_html:
            logger.error("❌ Failed to fetch main catalog page")
            return
        
        # Save debug file
        with open(DEBUG_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(catalog_html)
        logger.info(f"💾 Debug file saved: {DEBUG_FILE_PATH}")
        
        # Step 2: Parse catalog and extract products
        logger.info("🔍 Parsing catalog page for products...")
        products = await self._parse_catalog_page(catalog_html)
        
        if not products:
            logger.error("❌ No products found in catalog")
            return
        
        self.products = products
        logger.info(f"📦 Found {len(products)} products")
        
        # Step 3: Save product data
        await self._save_product_data()
        
        # Step 4: Download PDFs if any were found
        await self._download_product_pdfs()
        
        logger.info("=== BAUMIT A-Z Catalog Scraper Finished ===")
        self._log_summary()

    async def _save_product_data(self):
        """
        Save collected product data to JSON files.
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Complete products data
            products_file = PDF_STORAGE_DIR / f"baumit_products_data_{timestamp}.json"
            with open(products_file, 'w', encoding='utf-8') as f:
                json.dump(self.products, f, indent=2, ensure_ascii=False)
            
            # Readable summary
            summary_file = PDF_STORAGE_DIR / f"baumit_products_summary_{timestamp}.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("BAUMIT Products Summary\n")
                f.write("=" * 50 + "\n\n")
                
                for i, product in enumerate(self.products, 1):
                    f.write(f"{i}. {product.get('name', 'Unknown')}\n")
                    f.write(f"   Category: {product.get('category', 'N/A')}\n")
                    f.write(f"   URL: {product.get('url', 'N/A')}\n")
                    if product.get('pdf_links'):
                        f.write(f"   PDFs: {len(product['pdf_links'])} found\n")
                    f.write("\n")
            
            logger.info(f"💾 Product data saved:")
            logger.info(f"   📄 JSON: {products_file}")
            logger.info(f"   📋 Summary: {summary_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save product data: {e}")

    async def _download_product_pdfs(self):
        """
        Download PDFs found in product listings.
        """
        total_pdfs = sum(len(p.get('pdf_links', [])) for p in self.products)
        
        if total_pdfs == 0:
            logger.info("📥 No PDFs found for download")
            return
        
        logger.info(f"📥 Starting download of {total_pdfs} PDFs...")
        
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as session:
            download_tasks = []
            
            for product in self.products:
                pdf_links = product.get('pdf_links', [])
                product_name = product.get('name', 'Unknown')
                category = product.get('category', 'general')
                
                for pdf_url in pdf_links:
                    task = self._download_pdf(session, pdf_url, product_name, category)
                    download_tasks.append(task)
            
            if download_tasks:
                results = await asyncio.gather(*download_tasks, return_exceptions=True)
                
                successful = sum(1 for r in results if isinstance(r, dict) and r.get('status') == 'success')
                failed = len(results) - successful
                
                logger.info(f"📊 PDF Downloads: {successful} successful, {failed} failed")

    def _log_summary(self):
        """
        Logs the final summary with comprehensive statistics.
        """
        total_products = len(self.products)
        categories = {}
        
        for product in self.products:
            cat = product.get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        logger.info("=" * 60)
        logger.info("📊 BAUMIT A-Z CATALOG SCRAPER SUMMARY")
        logger.info("=" * 60)
        logger.info(f"📄 Total products found: {total_products}")
        logger.info(f"📁 Storage directory: {PDF_STORAGE_DIR.resolve()}")
        
        logger.info("\n📊 Products by Category:")
        for category, count in sorted(categories.items()):
            logger.info(f"   • {category}: {count} products")
        
        if self.downloaded_files:
            logger.info(f"\n📥 Downloaded files: {len(self.downloaded_files)}")
            logger.info(f"🔄 Duplicates: {self.duplicate_count}")
        
        logger.info("=" * 60)

async def run():
    """
    Runner function for the BAUMIT A-Z catalog scraper.
    """
    scraper = BaumitProductCatalogScraper()
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(run()) 