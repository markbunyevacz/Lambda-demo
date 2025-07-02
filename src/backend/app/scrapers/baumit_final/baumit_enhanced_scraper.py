"""
BAUMIT Enhanced Product Scraper
------------------------------

Purpose:
Enhanced scraper that handles dynamic content and JavaScript-heavy pages
to extract real BAUMIT products instead of navigation elements.

Key Features:
- Multiple URL strategies for finding products
- JavaScript content detection
- API endpoint discovery
- Alternative product discovery methods
- Real product extraction vs navigation filtering

This addresses the issue where the main catalog redirects and loads content dynamically.
"""
import asyncio
import logging
import json
import httpx
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path resolution fix for Docker compatibility
try:
    PROJECT_ROOT = Path(__file__).resolve().parents[5]
except IndexError:
    PROJECT_ROOT = Path(__file__).resolve().parents[3]

PDF_STORAGE_DIR = PROJECT_ROOT / "src" / "downloads" / "baumit_products"
ENHANCED_DIR = PDF_STORAGE_DIR / "enhanced_products"
DEBUG_DIR = PROJECT_ROOT / "debug_baumit"

# Ensure directories exist
PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
ENHANCED_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://baumit.hu"

# Alternative URLs to try for finding products
PRODUCT_URLS = [
    "https://baumit.hu/termekek",
    "https://baumit.hu/products", 
    "https://baumit.hu/hu/termekek",
    "https://baumit.hu/termekcsaladok",
    "https://baumit.hu/osszes-termek",
    "https://baumit.hu/product-search",
    "https://baumit.hu/api/products",  # Potential API endpoint
]

# BAUMIT product families to look for
BAUMIT_PRODUCT_FAMILIES = [
    'StarColor', 'PuraColor', 'SilikonColor', 'KlimaColor',
    'CreativTop', 'NanoporTop', 'KlimaTop', 'MultiTop',
    'GrundierSpachtel', 'FassadenSpachtel', 'AusgleichsSpachtel',
    'Ionit', 'Klima', 'Mineral', 'Silikon', 'Acrylic'
]

class BaumitEnhancedScraper:
    """
    Enhanced BAUMIT scraper with multiple strategies for finding real products.
    """
    
    def __init__(self):
        self.products = []
        self.api_endpoints = []
        self.visited_urls = set()
        self.real_products = []  # Filtered real products only
        
    async def _fetch_with_headers(self, url: str) -> Optional[str]:
        """Fetch content with enhanced headers and error handling."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'hu-HU,hu;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                logger.info(f"✅ Fetched {len(response.text)} chars from: {url}")
                return response.text
                
        except Exception as e:
            logger.error(f"❌ Failed to fetch {url}: {e}")
            return None

    def _find_api_endpoints(self, html_content: str) -> List[str]:
        """Extract potential API endpoints from JavaScript code."""
        endpoints = []
        
        # Look for common API patterns
        api_patterns = [
            r'["\'/]api/products["\']?',
            r'["\'/]products\.json["\']?',
            r'["\'/]search["\']?',
            r'["\'/]catalog["\']?',
            r'fetch\(["\']([^"\']*)["\']',
            r'axios\.get\(["\']([^"\']*)["\']',
            r'url:\s*["\']([^"\']*api[^"\']*)["\']',
            r'endpoint:\s*["\']([^"\']*)["\']'
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match[0] else match[1]
                
                if match and 'api' in match.lower() or 'product' in match.lower():
                    full_url = urljoin(BASE_URL, match.strip('\'"'))
                    if full_url not in endpoints:
                        endpoints.append(full_url)
        
        return endpoints

    def _is_real_product(self, name: str, description: str = "", url: str = "") -> bool:
        """
        Determine if this is a real product vs navigation/UI element.
        """
        text = f"{name} {description}".lower()
        
        # Filter out navigation/UI elements
        navigation_indicators = [
            'továbbiak betöltése', 'kevesebb betöltése', 'load more', 'show more',
            'összes', 'all', 'keresés', 'search', 'szűrő', 'filter',
            'a-z', 'betűrend', 'alphabet', 'abc', 'menu', 'navigation',
            'back', 'vissza', 'home', 'főoldal', 'next', 'previous',
            'első', 'last', 'utolsó', 'page', 'oldal'
        ]
        
        for indicator in navigation_indicators:
            if indicator in text:
                return False
        
        # Look for actual product indicators
        product_indicators = [
            'baumit', 'color', 'szín', 'festék', 'vakolat', 'szigetelő',
            'homlokzat', 'render', 'paint', 'insulation', 'facade',
            'mortar', 'adhesive', 'ragasztó', 'glett', 'filler'
        ]
        
        # Check if it looks like a product
        has_product_keyword = any(indicator in text for indicator in product_indicators)
        reasonable_length = 3 <= len(name) <= 50
        not_just_letters = not re.match(r'^[A-Z0-9-]+$', name.strip())
        
        return has_product_keyword and reasonable_length and not_just_letters

    async def _try_alternative_urls(self) -> List[Dict]:
        """Try multiple URLs to find actual products."""
        all_products = []
        
        for url in PRODUCT_URLS:
            logger.info(f"🔍 Trying alternative URL: {url}")
            
            html_content = await self._fetch_with_headers(url)
            if not html_content:
                continue
            
            # Save debug file for each URL
            url_slug = urlparse(url).path.replace('/', '_') or 'root'
            debug_file = DEBUG_DIR / f"baumit{url_slug}.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Look for API endpoints
            endpoints = self._find_api_endpoints(html_content)
            self.api_endpoints.extend(endpoints)
            
            # Extract products from this page
            products = await self._extract_products_from_content(html_content, url)
            all_products.extend(products)
            
            await asyncio.sleep(1)  # Be respectful
        
        return all_products

    async def _extract_products_from_content(self, html_content: str, source_url: str) -> List[Dict]:
        """Extract products from HTML content with improved filtering."""
        products = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try multiple selection strategies
            selectors = [
                'a[href*="termek"]',  # Links containing "termek" (product)
                'a[href*="product"]',
                '[data-product]',
                '.product-card, .product-item, .product-entry',
                'article',
                '.card',
                '[class*="product"]'
            ]
            
            found_elements = []
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    found_elements.extend(elements)
                    logger.info(f"📦 Found {len(elements)} elements with: {selector}")
            
            # Process found elements
            for element in found_elements[:100]:  # Limit processing
                try:
                    # Extract text and URL
                    text = element.get_text(strip=True)
                    href = element.get('href', '')
                    
                    if not text or len(text) < 3:
                        continue
                    
                    # Check if this looks like a real product
                    if not self._is_real_product(text, "", href):
                        continue
                    
                    product_url = urljoin(BASE_URL, href) if href else None
                    
                    # Check for product family keywords
                    family = None
                    for family_name in BAUMIT_PRODUCT_FAMILIES:
                        if family_name.lower() in text.lower():
                            family = family_name
                            break
                    
                    products.append({
                        'name': text[:100],  # Limit name length
                        'url': product_url,
                        'family': family,
                        'source_url': source_url,
                        'scraped_at': datetime.now().isoformat(),
                        'extraction_method': 'enhanced_filtering'
                    })
                    
                except Exception as e:
                    logger.warning(f"⚠️  Failed to process element: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"❌ Failed to extract from content: {e}")
        
        return products

    async def _try_api_endpoints(self) -> List[Dict]:
        """Try discovered API endpoints for product data."""
        api_products = []
        
        for endpoint in self.api_endpoints:
            logger.info(f"🔗 Trying API endpoint: {endpoint}")
            
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(endpoint)
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '')
                        
                        if 'json' in content_type:
                            data = response.json()
                            # Process JSON product data
                            # This would need to be adapted based on actual API structure
                            logger.info(f"✅ Got JSON response from: {endpoint}")
                            
                        else:
                            # HTML response from API endpoint
                            products = await self._extract_products_from_content(response.text, endpoint)
                            api_products.extend(products)
                            
            except Exception as e:
                logger.warning(f"⚠️  API endpoint failed {endpoint}: {e}")
                continue
        
        return api_products

    async def run(self):
        """Execute the enhanced BAUMIT scraping process."""
        logger.info("=== Starting BAUMIT Enhanced Product Scraper ===")
        
        # Step 1: Try alternative URLs
        logger.info("🔍 Phase 1: Trying alternative product URLs...")
        url_products = await self._try_alternative_urls()
        
        # Step 2: Try discovered API endpoints
        if self.api_endpoints:
            logger.info(f"🔗 Phase 2: Trying {len(self.api_endpoints)} API endpoints...")
            api_products = await self._try_api_endpoints()
            url_products.extend(api_products)
        
        # Step 3: Filter and deduplicate
        logger.info("🔍 Phase 3: Filtering real products...")
        seen_names = set()
        
        for product in url_products:
            name = product.get('name', '').strip()
            if name and name not in seen_names:
                if self._is_real_product(name):
                    self.real_products.append(product)
                    seen_names.add(name)
        
        # Step 4: Save results
        await self._save_enhanced_results()
        
        logger.info("=== BAUMIT Enhanced Scraper Finished ===")
        self._log_enhanced_summary()

    async def _save_enhanced_results(self):
        """Save enhanced scraping results."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # All found products
            all_file = ENHANCED_DIR / f"baumit_all_products_{timestamp}.json"
            with open(all_file, 'w', encoding='utf-8') as f:
                json.dump(self.products, f, indent=2, ensure_ascii=False)
            
            # Real products only
            real_file = ENHANCED_DIR / f"baumit_real_products_{timestamp}.json"
            with open(real_file, 'w', encoding='utf-8') as f:
                json.dump(self.real_products, f, indent=2, ensure_ascii=False)
            
            # Human-readable summary
            summary_file = ENHANCED_DIR / f"baumit_enhanced_summary_{timestamp}.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("BAUMIT Enhanced Scraper Results\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"Total elements found: {len(self.products)}\n")
                f.write(f"Real products identified: {len(self.real_products)}\n")
                f.write(f"API endpoints discovered: {len(self.api_endpoints)}\n\n")
                
                f.write("API Endpoints Found:\n")
                for endpoint in self.api_endpoints:
                    f.write(f"  - {endpoint}\n")
                f.write("\n")
                
                f.write("Real Products:\n")
                f.write("-" * 30 + "\n")
                for i, product in enumerate(self.real_products, 1):
                    f.write(f"{i}. {product.get('name', 'Unknown')}\n")
                    if product.get('family'):
                        f.write(f"   Family: {product['family']}\n")
                    if product.get('url'):
                        f.write(f"   URL: {product['url']}\n")
                    f.write(f"   Source: {product.get('source_url', 'Unknown')}\n")
                    f.write("\n")
            
            logger.info(f"💾 Enhanced results saved:")
            logger.info(f"   📄 Real products: {real_file}")
            logger.info(f"   📋 Summary: {summary_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save enhanced results: {e}")

    def _log_enhanced_summary(self):
        """Log enhanced scraper summary."""
        families = {}
        for product in self.real_products:
            family = product.get('family', 'Unknown')
            families[family] = families.get(family, 0) + 1
        
        logger.info("=" * 60)
        logger.info("📊 BAUMIT ENHANCED SCRAPER SUMMARY")
        logger.info("=" * 60)
        logger.info(f"🔗 API endpoints found: {len(self.api_endpoints)}")
        logger.info(f"📦 Real products found: {len(self.real_products)}")
        logger.info(f"📁 Storage: {ENHANCED_DIR}")
        
        if families:
            logger.info("\n📊 Products by Family:")
            for family, count in sorted(families.items()):
                logger.info(f"   • {family}: {count} products")
        
        logger.info("=" * 60)

async def run():
    """Runner function for enhanced BAUMIT scraper."""
    scraper = BaumitEnhancedScraper()
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(run()) 