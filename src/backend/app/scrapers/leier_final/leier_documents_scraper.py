"""
LEIER Documents Scraper - High Priority Implementation
----------------------------------------------------

This scraper targets the main LEIER downloadable documents section
and systematically collects technical datasheets, installation guides,
CAD files, and product catalogs from all 24+ product categories.

Entry Point: https://www.leier.hu/hu/letoltheto-dokumentumok
Architecture: BrightData MCP + BeautifulSoup + Async Downloads
Priority: HIGH - Essential for LEIER data collection
"""

import asyncio
import logging
import json
import httpx
import re
import hashlib
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import os
from typing import List, Optional, Set
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Path configuration - Fixed for Lambda project structure
PROJECT_ROOT = Path(__file__).resolve().parents[5]  # Go up to Lambda/ root
BASE_STORAGE = PROJECT_ROOT / "src" / "downloads" / "leier_materials"
DUPLICATES_DIR = BASE_STORAGE / "duplicates"

# Create organized storage structure
STORAGE_DIRS = {
    'datasheets': BASE_STORAGE / "technical_datasheets",
    'guides': BASE_STORAGE / "installation_guides",
    'cad': BASE_STORAGE / "cad_files", 
    'catalogs': BASE_STORAGE / "product_catalogs",
    'calculators': BASE_STORAGE / "calculators",
    'pricing': BASE_STORAGE / "pricing_data"
}

# Ensure all directories exist
for storage_dir in STORAGE_DIRS.values():
    storage_dir.mkdir(parents=True, exist_ok=True)
DUPLICATES_DIR.mkdir(parents=True, exist_ok=True)

# LEIER website configuration
BASE_URL = "https://www.leier.hu"
MAIN_DOCS_URL = "https://www.leier.hu/hu/letoltheto-dokumentumok"

# Document classification patterns
DOC_PATTERNS = {
    'datasheets': [
        r'műszaki.*adatlap', r'technical.*datasheet', 
        r'termék.*adatlap', r'adatlap'
    ],
    'guides': [
        r'beépítési.*útmutató', r'installation.*guide', 
        r'szerelési', r'útmutató', r'guide'
    ],
    'cad': [r'\.dwg$', r'\.dxf$', r'cad', r'rajz', r'drawing'],
    'catalogs': [r'katalógus', r'catalog', r'prospektus', r'brosúra'],
    'calculators': [r'kalkulátor', r'calculator', r'számológép', r'kalku'],
    'pricing': [r'árlista', r'pricelist', r'ár.*táj', r'price']
}


@dataclass
class LeierDoc:
    """LEIER document data structure"""
    name: str
    url: str
    doc_type: str
    file_ext: str
    category: str = "general"
    size: Optional[int] = None


class LeierDocumentsScraper:
    """Main LEIER documents scraper with comprehensive coverage"""
    
    def __init__(self):
        self.documents: List[LeierDoc] = []
        self.visited_urls: Set[str] = set()
        self.downloaded_files: Set[str] = set()
        self.stats = {
            'categories_found': 0,
            'docs_discovered': 0,
            'downloads_success': 0,
            'downloads_failed': 0,
            'duplicates': 0
        }
    
    async def fetch_page_content(self, url: str) -> Optional[str]:
        """Fetch page content with BrightData MCP fallback to direct HTTP"""
        try:
            # Try BrightData MCP first
            return await self._fetch_with_mcp(url)
        except Exception as e:
            logger.warning(f"MCP failed for {url}, using direct fetch: {e}")
            return await self._fetch_direct(url)
    
    async def _fetch_with_mcp(self, url: str) -> Optional[str]:
        """Fetch using BrightData MCP"""
        try:
            from mcp import stdio_client, StdioServerParameters, ClientSession
            import platform
            
            npx_cmd = "npx.cmd" if platform.system() == "Windows" else "npx"
            api_token = os.getenv('BRIGHTDATA_API_TOKEN')
            
            if not api_token:
                raise ValueError("No BRIGHTDATA_API_TOKEN found")
            
            server_params = StdioServerParameters(
                command=npx_cmd,
                env={"API_TOKEN": api_token},
                args=["-y", "@brightdata/mcp"]
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    tools = await session.list_tools()
                    scrape_tool = None
                    
                    for tool in tools.tools:
                        if 'scrape' in tool.name.lower() and 'html' in tool.name.lower():
                            scrape_tool = tool
                            break
                    
                    if scrape_tool:
                        response = await session.call_tool(scrape_tool.name, {"url": url})
                        if response.content:
                            return response.content[0].text
            
            return None
            
        except Exception as e:
            logger.debug(f"MCP fetch error: {e}")
            raise
    
    async def _fetch_direct(self, url: str) -> Optional[str]:
        """Direct HTTP fetch as fallback"""
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"Direct fetch failed for {url}: {e}")
            return None
    
    def classify_document(self, name: str, url: str) -> str:
        """Classify document into appropriate category"""
        name_lower = name.lower()
        url_lower = url.lower()
        
        for doc_type, patterns in DOC_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, name_lower) or re.search(pattern, url_lower):
                    return doc_type
        
        # File extension based classification
        if url_lower.endswith(('.dwg', '.dxf')):
            return 'cad'
        elif any(word in name_lower for word in ['műszaki', 'technical', 'adatlap']):
            return 'datasheets'
        elif any(word in name_lower for word in ['útmutató', 'guide', 'manual']):
            return 'guides'
        
        return 'catalogs'  # Default category
    
    async def discover_categories(self) -> List[str]:
        """Discover all LEIER product categories"""
        logger.info("🔍 Discovering LEIER categories...")
        
        content = await self.fetch_page_content(MAIN_DOCS_URL)
        if not content:
            logger.error("Failed to fetch main documents page")
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        category_urls = set()
        
        # Look for category navigation links
        selectors = [
            'a[href*="/termekek/"]',
            'a[href*="/kategoria/"]',
            '.category-link',
            '.nav-link[href*="/hu/"]',
            '.menu-item a'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(BASE_URL, href)
                    if self._is_valid_category_url(full_url):
                        category_urls.add(full_url)
        
        categories = list(category_urls)[:30]  # Limit to reasonable number
        logger.info(f"📂 Found {len(categories)} categories to process")
        return categories
    
    def _is_valid_category_url(self, url: str) -> bool:
        """Check if URL is a valid category URL"""
        url_lower = url.lower()
        return (
            url.startswith(BASE_URL) and
            any(keyword in url_lower for keyword in [
                'termek', 'kategoria', 'letoltheto', 'dokumentum'
            ]) and
            url not in self.visited_urls
        )
    
    async def extract_documents_from_page(self, url: str) -> List[LeierDoc]:
        """Extract document links from a category page"""
        if url in self.visited_urls:
            return []
        
        self.visited_urls.add(url)
        logger.info(f"📄 Extracting documents from: {url}")
        
        content = await self.fetch_page_content(url)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        documents = []
        
        # Extract category name from URL or page content
        category = self._extract_category_name(url, soup)
        
        # Document link selectors
        doc_selectors = [
            'a[href$=".pdf"]', 'a[href$=".dwg"]', 'a[href$=".dxf"]',
            'a[href$=".doc"]', 'a[href$=".docx"]', 'a[href$=".xls"]',
            'a[href$=".xlsx"]', '.download-link', 'a[download]'
        ]
        
        for selector in doc_selectors:
            links = soup.select(selector)
            for link in links:
                doc_url = link.get('href')
                if not doc_url:
                    continue
                
                doc_url = urljoin(BASE_URL, doc_url)
                doc_name = (
                    link.get('download') or 
                    link.get('title') or 
                    link.text.strip() or 
                    Path(doc_url).name
                )
                
                if doc_name and len(doc_name.strip()) > 0:
                    file_ext = Path(doc_url).suffix.lower()[1:]  # Remove dot
                    doc_type = self.classify_document(doc_name, doc_url)
                    
                    document = LeierDoc(
                        name=doc_name[:80].strip(),  # Limit length
                        url=doc_url,
                        doc_type=doc_type,
                        file_ext=file_ext,
                        category=category
                    )
                    
                    documents.append(document)
        
        logger.info(f"✅ Found {len(documents)} documents in {category}")
        return documents
    
    def _extract_category_name(self, url: str, soup: BeautifulSoup) -> str:
        """Extract category name from URL or page content"""
        # Try URL path
        path_parts = [p for p in urlparse(url).path.split('/') if p and len(p) > 2]
        if path_parts:
            return path_parts[-1].replace('-', ' ').title()
        
        # Try page title/heading
        title_selectors = ['h1', '.page-title', '.category-title', 'title']
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) < 50:
                    return title
        
        return "General"
    
    def generate_safe_filename(self, doc: LeierDoc) -> str:
        """Generate safe filename with duplicate handling"""
        # Clean name
        safe_name = re.sub(r'[^\w\s.-]', '', doc.name)
        safe_name = safe_name.strip()[:40]  # Limit length
        
        # Add extension if missing
        if doc.file_ext and not safe_name.endswith(f'.{doc.file_ext}'):
            filename = f"{safe_name}.{doc.file_ext}"
        else:
            filename = safe_name
        
        # Handle duplicates
        if filename in self.downloaded_files:
            url_hash = hashlib.md5(doc.url.encode()).hexdigest()[:6]
            name_part, ext_part = os.path.splitext(filename)
            filename = f"{name_part}_{url_hash}{ext_part}"
            self.stats['duplicates'] += 1
        
        self.downloaded_files.add(filename)
        return filename
    
    async def download_document(self, session: httpx.AsyncClient, doc: LeierDoc) -> dict:
        """Download a single document"""
        try:
            filename = self.generate_safe_filename(doc)
            storage_dir = STORAGE_DIRS.get(doc.doc_type, STORAGE_DIRS['catalogs'])
            filepath = storage_dir / filename
            
            logger.info(f"⬇️  Downloading: {doc.name} -> {doc.doc_type}/{filename}")
            
            response = await session.get(doc.url, follow_redirects=True)
            response.raise_for_status()
            
            # Save file
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            self.stats['downloads_success'] += 1
            
            return {
                'status': 'success',
                'filename': filename,
                'path': str(filepath),
                'size': len(response.content),
                'category': doc.doc_type
            }
            
        except Exception as e:
            logger.error(f"❌ Download failed for {doc.name}: {e}")
            self.stats['downloads_failed'] += 1
            return {'status': 'failed', 'error': str(e)}
    
    async def download_all_documents(self):
        """Download all discovered documents"""
        if not self.documents:
            logger.warning("⚠️  No documents to download")
            return
        
        logger.info(f"📥 Starting download of {len(self.documents)} documents...")
        
        async with httpx.AsyncClient(timeout=60.0) as session:
            semaphore = asyncio.Semaphore(3)  # Limit concurrent downloads
            
            async def download_with_limit(doc):
                async with semaphore:
                    return await self.download_document(session, doc)
            
            tasks = [download_with_limit(doc) for doc in self.documents]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Download task exception: {result}")
                    self.stats['downloads_failed'] += 1
    
    async def run_full_scrape(self):
        """Execute complete LEIER documents scraping"""
        start_time = datetime.now()
        
        logger.info("🚀 LEIER Documents Scraper Starting")
        logger.info("=" * 50)
        
        try:
            # Step 1: Discover categories
            categories = await self.discover_categories()
            self.stats['categories_found'] = len(categories)
            
            if not categories:
                logger.error("❌ No categories found - check website structure")
                return
            
            # Step 2: Extract documents from all categories  
            logger.info(f"📂 Processing {len(categories)} categories...")
            all_docs = []
            
            for i, category_url in enumerate(categories, 1):
                logger.info(f"📂 Category {i}/{len(categories)}: {category_url}")
                docs = await self.extract_documents_from_page(category_url)
                all_docs.extend(docs)
                
                # Rate limiting
                await asyncio.sleep(0.5)
            
            self.documents = all_docs
            self.stats['docs_discovered'] = len(all_docs)
            
            # Step 3: Download all documents
            if self.documents:
                await self.download_all_documents()
            
            # Step 4: Generate report
            self.generate_final_report(start_time)
            
        except Exception as e:
            logger.error(f"❌ Scraping failed: {e}")
            raise
    
    def generate_final_report(self, start_time: datetime):
        """Generate comprehensive final report"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Document type breakdown
        type_counts = {}
        for doc in self.documents:
            type_counts[doc.doc_type] = type_counts.get(doc.doc_type, 0) + 1
        
        logger.info("=" * 70)
        logger.info("📊 LEIER DOCUMENTS SCRAPER - FINAL REPORT")
        logger.info("=" * 70)
        
        # Overall stats
        logger.info(f"⏱️  Duration: {duration:.1f} seconds")
        logger.info(f"🗂️  Categories processed: {self.stats['categories_found']}")
        logger.info(f"📄 Documents discovered: {self.stats['docs_discovered']}")
        logger.info(f"✅ Downloads successful: {self.stats['downloads_success']}")
        logger.info(f"❌ Downloads failed: {self.stats['downloads_failed']}")
        logger.info(f"🔄 Duplicates handled: {self.stats['duplicates']}")
        
        # Breakdown by type
        logger.info("\n📊 Documents by Type:")
        for doc_type, count in type_counts.items():
            storage_dir = STORAGE_DIRS.get(doc_type, 'unknown')
            logger.info(f"   {doc_type}: {count} -> {storage_dir}")
        
        logger.info("=" * 70)
        
        # Save JSON report
        self.save_json_report(start_time, end_time, type_counts)
    
    def save_json_report(self, start_time: datetime, end_time: datetime, type_counts: dict):
        """Save detailed JSON report"""
        report = {
            'scraper_info': {
                'name': 'LEIER Documents Scraper',
                'version': '1.0',
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': (end_time - start_time).total_seconds()
            },
            'statistics': self.stats,
            'type_breakdown': type_counts,
            'storage_locations': {k: str(v) for k, v in STORAGE_DIRS.items()},
            'documents': [
                {
                    'name': doc.name,
                    'url': doc.url,
                    'type': doc.doc_type,
                    'extension': doc.file_ext,
                    'category': doc.category
                }
                for doc in self.documents
            ]
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = PROJECT_ROOT / f"leier_scraping_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 Report saved: {report_file}")


async def main():
    """Main entry point for LEIER documents scraper"""
    scraper = LeierDocumentsScraper()
    await scraper.run_full_scrape()


if __name__ == "__main__":
    asyncio.run(main()) 