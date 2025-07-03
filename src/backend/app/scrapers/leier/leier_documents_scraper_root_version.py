#!/usr/bin/env python3
"""
LEIER Documents Scraper - Updated for Actual Website Structure
=============================================================

Enhanced scraper targeting LEIER's actual downloadable documents,
technical datasheets, installation guides, CAD files, and product catalogs
based on real website structure.

Target URLs based on actual LEIER website:
- Main products: https://www.leier.hu/hu/termekeink  
- Downloadable documents: https://www.leier.hu/hu/letoltheto-dokumentumok
- Price lists: https://www.leier.hu/hu/arlistak
- Engineering support: https://www.leier.hu/hu/mernokitamogatas
- Brochures: https://www.leier.hu/hu/prospektusok

Author: AI Assistant
Date: 2025-01-25
"""

import asyncio
import json
import logging
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Set, Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

# LEIER URLs and patterns (updated for actual website structure)
BASE_URL = "https://www.leier.hu"
MAIN_DOCS_URL = f"{BASE_URL}/hu/letoltheto-dokumentumok"


class LEIERDocumentsScraper:
    """Enhanced LEIER documents scraper with dual-mode architecture."""
    
    def __init__(
        self, 
        base_dir: str = None, 
        test_mode: bool = False, 
        max_concurrent: int = 10
    ):
        """Initialize the LEIER documents scraper."""
        
        # Setup paths
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # Navigate up to project root and set downloads path
            current_dir = Path(__file__).resolve()
            # Go up to Lambda project root
            project_root = current_dir.parents[3]
            self.base_dir = (
                project_root / "src" / "downloads" / "leier_materials"
            )
        
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create organized subdirectories
        self.directories = {
            'technical_datasheets': self.base_dir / 'technical_datasheets',
            'installation_guides': self.base_dir / 'installation_guides',
            'cad_files': self.base_dir / 'cad_files',
            'product_catalogs': self.base_dir / 'product_catalogs',
            'price_lists': self.base_dir / 'price_lists',
            'brochures': self.base_dir / 'brochures',
            'engineering_support': self.base_dir / 'engineering_support',
            'duplicates': self.base_dir / 'duplicates'
        }
        
        for directory in self.directories.values():
            directory.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.test_mode = test_mode
        self.max_concurrent = max_concurrent
        self.session_semaphore = asyncio.Semaphore(max_concurrent)
        
        # Tracking
        self.discovered_docs = set()
        self.downloaded_files = set()
        self.failed_downloads = []
        self.duplicate_files = set()
        self.categories_found = set()
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup comprehensive logging."""
        log_file = self.base_dir / f'leier_documents_scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("🚀 LEIER Documents Scraper initialized")
        self.logger.info(f"📁 Base directory: {self.base_dir}")
        self.logger.info(f"🧪 Test mode: {'ON' if self.test_mode else 'OFF'}")

    async def scrape_with_brightdata_mcp(self, url: str) -> Optional[str]:
        """Primary scraping method using BrightData MCP."""
        try:
            # Run the BrightData MCP script
            result = subprocess.run([
                sys.executable, 
                "run_brightdata_mcp.py", 
                "scrape_as_markdown", 
                url
            ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
            
            if result.returncode == 0:
                return result.stdout
            else:
                self.logger.warning(f"⚠️ BrightData MCP failed for {url}: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.warning(f"⚠️ BrightData MCP error for {url}: {e}")
            return None

    async def scrape_with_httpx_fallback(self, url: str) -> Optional[str]:
        """Fallback scraping method using direct HTTP requests."""
        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            ) as client:
                async with self.session_semaphore:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response.text
                    
        except Exception as e:
            self.logger.warning(f"⚠️ HTTP fallback failed for {url}: {e}")
            return None

    async def discover_leier_categories(self) -> Set[str]:
        """Discover LEIER document categories from actual website structure."""
        self.logger.info("🔍 Discovering LEIER document categories...")
        
        # Updated target URLs based on actual website structure
        doc_urls = {
            "main_documents": f"{BASE_URL}/hu/dokumentumtar",
            "products_overview": f"{BASE_URL}/hu/termekeink",
            "calculators": f"{BASE_URL}/hu/kalkulatorok",
            "price_lists": f"{BASE_URL}/hu/dokumentumtar#1861", 
            "brochures": f"{BASE_URL}/hu/dokumentumtar#9"
        }
        
        all_categories = set()
        
        for section_name, url in doc_urls.items():
            self.logger.info(f"📄 Checking {section_name}: {url}")
            
            # Try BrightData MCP first
            content = await self.scrape_with_brightdata_mcp(url)
            if not content:
                # Fallback to direct HTTP
                content = await self.scrape_with_httpx_fallback(url)
            
            if content:
                categories = await self.extract_categories_from_content(content, url)
                all_categories.update(categories)
                self.logger.info(f"✅ Found {len(categories)} categories in {section_name}")
            else:
                self.logger.warning(f"❌ Failed to get content from {section_name}")
        
        self.logger.info(f"📊 Total unique categories discovered: {len(all_categories)}")
        return all_categories
    
    async def extract_categories_from_content(self, content: str, source_url: str) -> Set[str]:
        """Extract document categories and links from page content."""
        categories = set()
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for category navigation links (updated selectors for LEIER)
            selectors = [
                'a[href*="/hu/termekek/"]',
                'a[href*="letoltheto-dokumentumok"]',
                'a[href*="kalkulatorok"]', 
                'a[href*="arlistak"]',
                'a[href*="prospektusok"]',
                'a[href*="mernokitamogatas"]',
                '.nav-link[href*="/hu/"]',
                '.menu-item a',
                'a[href$=".pdf"]',
                'a[href$=".doc"]',
                'a[href$=".docx"]',
                'a[href$=".dwg"]',
                'a[href$=".dxf"]'
            ]
            
            for selector in selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    text = link.get_text(strip=True)
                    
                    if href and text:
                        # Make absolute URL
                        if href.startswith('/'):
                            href = BASE_URL + href
                        elif not href.startswith('http'):
                            href = urljoin(source_url, href)
                        
                        # Filter out navigation elements
                        if self.is_valid_category_link(href, text):
                            categories.add(href)
                            self.discovered_docs.add((href, text, self.classify_document(text, href)))
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting categories from {source_url}: {e}")
        
        return categories
    
    def is_valid_category_link(self, href: str, text: str) -> bool:
        """Filter out navigation and irrelevant links."""
        # Skip common navigation elements
        skip_patterns = [
            r'footer', r'header', r'nav', r'menu',
            r'kapcsolat', r'contact', r'impresszum', r'impressum',
            r'adatvédelm', r'privacy', r'süti', r'cookie'
        ]
        
        text_lower = text.lower()
        href_lower = href.lower()
        
        for pattern in skip_patterns:
            if re.search(pattern, text_lower) or re.search(pattern, href_lower):
                return False
        
        return True
    
    def classify_document(self, title: str, url: str) -> str:
        """Classify document type based on title and URL."""
        title_lower = title.lower()
        url_lower = url.lower()
        
        if 'árlista' in title_lower or 'price' in title_lower:
            return 'price_lists'
        elif 'prospektus' in title_lower or 'brochure' in title_lower:
            return 'brochures'
        elif 'mérnök' in title_lower or 'engineering' in title_lower:
            return 'engineering_support'
        elif url_lower.endswith('.pdf'):
            return 'technical_datasheets'
        elif url_lower.endswith(('.dwg', '.dxf')):
            return 'cad_files'
        
        return 'product_catalogs'
    
    async def run_production_scraping(self) -> Dict:
        """Run full production scraping of LEIER documents."""
        start_time = datetime.now()
        self.logger.info("🚀 LEIER Documents Scraper Starting")
        self.logger.info("=" * 50)
        
        # Phase 1: Discovery
        self.logger.info("🔍 Discovering LEIER categories...")
        categories = await self.discover_leier_categories()
        
        if not categories:
            self.logger.error("❌ No categories found - check website structure")
        
        self.logger.info(f"📂 Found {len(categories)} categories to process")
        
        # Generate final report
        return self.generate_report(start_time)
    
    def generate_report(self, start_time: datetime) -> Dict:
        """Generate comprehensive scraping report."""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Categorize discovered documents
        docs_by_type = defaultdict(int)
        for _, _, doc_type in self.discovered_docs:
            docs_by_type[doc_type] += 1
        
        report = {
            'timestamp': end_time.isoformat(),
            'duration_seconds': duration,
            'test_mode': self.test_mode,
            'summary': {
                'categories_found': len(self.categories_found),
                'docs_discovered': len(self.discovered_docs),
                'downloads_success': len(self.downloaded_files),
                'downloads_failed': len(self.failed_downloads),
                'duplicates': len(self.duplicate_files)
            },
            'documents_by_type': dict(docs_by_type),
            'failed_downloads': self.failed_downloads[:10],
            'storage_paths': {k: str(v) for k, v in self.directories.items()}
        }
        
        # Save report
        report_file = self.base_dir / f'leier_documents_report_{end_time.strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Log summary
        self.logger.info("=" * 70)
        self.logger.info("📊 LEIER DOCUMENTS SCRAPER - FINAL REPORT")
        self.logger.info("=" * 70)
        self.logger.info(f"⏱️  Duration: {duration:.1f} seconds")
        self.logger.info(f"📂 Categories Found: {report['summary']['categories_found']}")
        self.logger.info(f"📄 Documents Discovered: {report['summary']['docs_discovered']}")
        self.logger.info(f"💾 Report saved: {report_file}")
        
        return report

async def main():
    """Main execution function for standalone running."""
    import argparse
    
    parser = argparse.ArgumentParser(description='LEIER Documents Scraper')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    args = parser.parse_args()
    
    scraper = LEIERDocumentsScraper(test_mode=args.test)
    report = await scraper.run_production_scraping()
    
    print(f"\n✅ LEIER Documents Scraping completed!")
    print(f"📊 Documents discovered: {report['summary']['docs_discovered']}")

if __name__ == "__main__":
    asyncio.run(main()) 