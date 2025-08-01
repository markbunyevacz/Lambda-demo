"""
Real Rockwool Scraper Implementation

This scraper provides production-ready data collection from the Rockwool website.
Replaces any mock or placeholder scrapers with real web scraping functionality.
"""

import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import json
import re
from ..config.settings import settings


@dataclass
class RockwoolProduct:
    """Data class for Rockwool product information."""
    name: str
    description: str
    category: str
    subcategory: Optional[str]
    url: str
    technical_specs: Dict[str, Any]
    applications: List[str]
    images: List[str]
    documents: List[Dict[str, str]]
    manufacturer: str = "ROCKWOOL"
    

class RockwoolScraper:
    """
    Production scraper for ROCKWOOL building materials data.
    
    This scraper collects real product data from the official ROCKWOOL website,
    ensuring no mock or placeholder data is used.
    """
    
    def __init__(self):
        """Initialize the scraper with production settings."""
        self.base_url = "https://www.rockwool.com"
        self.session: Optional[aiohttp.ClientSession] = None
        self.scraped_products: List[RockwoolProduct] = []
        self.delay_between_requests = 2.0  # Respectful scraping delay
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a webpage with proper error handling and rate limiting.
        
        Args:
            url: URL to fetch
            
        Returns:
            Page content or None if error
        """
        try:
            await asyncio.sleep(self.delay_between_requests)
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    self.logger.info(f"Successfully fetched: {url}")
                    return content
                else:
                    self.logger.warning(f"HTTP {response.status} for {url}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None
    
    def _extract_technical_specs(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract technical specifications from product page.
        
        Args:
            soup: BeautifulSoup object of the product page
            
        Returns:
            Dictionary of technical specifications
        """
        specs = {}
        
        try:
            # Look for technical data tables
            spec_tables = soup.find_all(['table', 'div'], class_=re.compile(r'spec|tech|data|property', re.I))
            
            for table in spec_tables:
                rows = table.find_all(['tr', 'div'])
                
                for row in rows:
                    cells = row.find_all(['td', 'th', 'span', 'div'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        
                        if key and value:
                            # Normalize key names to Hungarian
                            normalized_key = self._normalize_spec_key(key)
                            if normalized_key:
                                specs[normalized_key] = self._parse_spec_value(value)
            
            # Look for specific ROCKWOOL characteristics
            content_text = soup.get_text().lower()
            
            # Fire classification
            if 'a1' in content_text or 'nem éghető' in content_text:
                specs['tűzvédelmi_osztály'] = 'A1 (nem éghető)'
            
            # Melting point
            if '1000°c' in content_text or '1000 °c' in content_text:
                specs['olvadáspont'] = '> 1000°C'
                
            # Water repellent
            if 'víztaszító' in content_text or 'water repellent' in content_text:
                specs['víztaszító'] = 'igen'
                
            return specs
            
        except Exception as e:
            self.logger.error(f"Error extracting specs: {e}")
            return {}
    
    def _normalize_spec_key(self, key: str) -> Optional[str]:
        """Normalize specification key to Hungarian standard format."""
        key_lower = key.lower()
        
        # Thermal conductivity
        if any(term in key_lower for term in ['thermal conductivity', 'hővezetési', 'λ']):
            return 'hővezetési_tényező'
        # Fire classification
        elif any(term in key_lower for term in ['fire class', 'tűzvédel', 'fire rating']):
            return 'tűzvédelmi_osztály'
        # Compressive strength
        elif any(term in key_lower for term in ['compressive', 'nyomó', 'compression']):
            return 'nyomószilárdság'
        # Density
        elif any(term in key_lower for term in ['density', 'sűrűség', 'testsűrűség']):
            return 'testsűrűség'
        # Thickness
        elif any(term in key_lower for term in ['thickness', 'vastagság']):
            return 'vastagság'
        # Water absorption
        elif any(term in key_lower for term in ['water absorption', 'vízfelvétel']):
            return 'vízfelvétel'
        
        return None
    
    def _parse_spec_value(self, value: str) -> Dict[str, str]:
        """Parse specification value to extract numeric value and unit."""
        # Extract numeric value and unit
        match = re.search(r'([0-9.,]+)\s*([a-zA-Z/°%]+)', value)
        if match:
            return {
                'érték': match.group(1),
                'mértékegység': match.group(2)
            }
        else:
            return {'érték': value, 'mértékegység': ''}
    
    async def _extract_product_details(self, product_url: str) -> Optional[RockwoolProduct]:
        """
        Extract detailed product information from a product page.
        
        Args:
            product_url: URL of the product page
            
        Returns:
            RockwoolProduct object or None if extraction fails
        """
        try:
            content = await self._fetch_page(product_url)
            if not content:
                return None
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract product name
            name_selectors = ['h1', '.product-title', '.page-title', '[data-product-name]']
            name = ""
            for selector in name_selectors:
                element = soup.select_one(selector)
                if element:
                    name = element.get_text(strip=True)
                    break
            
            # Extract description
            desc_selectors = ['.product-description', '.description', '.intro', '.summary']
            description = ""
            for selector in desc_selectors:
                element = soup.select_one(selector)
                if element:
                    description = element.get_text(strip=True)
                    break
            
            # Extract technical specifications
            technical_specs = self._extract_technical_specs(soup)
            
            # Extract images
            images = []
            img_elements = soup.find_all('img')
            for img in img_elements:
                src = img.get('src') or img.get('data-src')
                if src and any(term in src.lower() for term in ['product', 'material', 'rockwool']):
                    full_url = urljoin(product_url, src)
                    images.append(full_url)
            
            # Extract documents/datasheets
            documents = []
            doc_links = soup.find_all('a', href=re.compile(r'\.(pdf|doc|docx)$', re.I))
            for link in doc_links:
                href = link.get('href')
                text = link.get_text(strip=True)
                if href:
                    documents.append({
                        'title': text or 'Dokumentum',
                        'url': urljoin(product_url, href),
                        'type': 'PDF' if href.lower().endswith('.pdf') else 'Document'
                    })
            
            # Determine category from URL or content
            category = self._determine_category(product_url, soup)
            
            # Extract applications
            applications = self._extract_applications(soup)
            
            product = RockwoolProduct(
                name=name or "Ismeretlen ROCKWOOL termék",
                description=description or "Nincs leírás elérhető",
                category=category,
                subcategory=None,
                url=product_url,
                technical_specs=technical_specs,
                applications=applications,
                images=images[:5],  # Limit to 5 images
                documents=documents[:10]  # Limit to 10 documents
            )
            
            self.logger.info(f"Extracted product: {product.name}")
            return product
            
        except Exception as e:
            self.logger.error(f"Error extracting product from {product_url}: {e}")
            return None
    
    def _determine_category(self, url: str, soup: BeautifulSoup) -> str:
        """Determine product category from URL and page content."""
        url_lower = url.lower()
        
        if 'insulation' in url_lower or 'szigetel' in url_lower:
            if 'facade' in url_lower or 'homlokzat' in url_lower:
                return 'Homlokzati hőszigetelés'
            elif 'roof' in url_lower or 'tető' in url_lower:
                return 'Tetőszigetelés'
            elif 'wall' in url_lower or 'fal' in url_lower:
                return 'Falszigetelés'
            else:
                return 'Hőszigetelő anyagok'
        elif 'acoustic' in url_lower or 'hangszigel' in url_lower:
            return 'Hangszigetelő anyagok'
        elif 'marine' in url_lower:
            return 'Hajóipari szigetelés'
        elif 'industrial' in url_lower or 'ipari' in url_lower:
            return 'Ipari szigetelés'
        else:
            return 'ROCKWOOL termékek'
    
    def _extract_applications(self, soup: BeautifulSoup) -> List[str]:
        """Extract application areas from product page."""
        applications = []
        
        # Look for application sections
        app_sections = soup.find_all(['div', 'section'], class_=re.compile(r'application|use|alkalmazás', re.I))
        
        for section in app_sections:
            items = section.find_all(['li', 'p', 'div'])
            for item in items:
                text = item.get_text(strip=True)
                if text and len(text) > 10 and len(text) < 100:
                    applications.append(text)
        
        return applications[:5]  # Limit to 5 applications
    
    async def scrape_products_from_sitemap(self) -> List[RockwoolProduct]:
        """
        Scrape products by finding product URLs from sitemap or navigation.
        
        Returns:
            List of scraped RockwoolProduct objects
        """
        try:
            # Try to get sitemap first
            sitemap_urls = [
                f"{self.base_url}/sitemap.xml",
                f"{self.base_url}/sitemap_index.xml",
                f"{self.base_url}/robots.txt"
            ]
            
            product_urls = []
            
            for sitemap_url in sitemap_urls:
                content = await self._fetch_page(sitemap_url)
                if content:
                    # Extract product URLs from sitemap
                    urls = re.findall(r'<loc>(.*?)</loc>', content)
                    for url in urls:
                        if any(term in url.lower() for term in ['product', 'insulation', 'material']):
                            product_urls.append(url)
                    
                    if product_urls:
                        break
            
            # If no sitemap, try navigation pages
            if not product_urls:
                nav_pages = [
                    f"{self.base_url}/products",
                    f"{self.base_url}/insulation",
                    f"{self.base_url}/building-insulation"
                ]
                
                for nav_url in nav_pages:
                    content = await self._fetch_page(nav_url)
                    if content:
                        soup = BeautifulSoup(content, 'html.parser')
                        links = soup.find_all('a', href=True)
                        
                        for link in links:
                            href = link['href']
                            if any(term in href.lower() for term in ['product', 'insulation']) and href not in product_urls:
                                full_url = urljoin(self.base_url, href)
                                product_urls.append(full_url)
            
            # Limit to reasonable number for production
            product_urls = product_urls[:50]
            
            self.logger.info(f"Found {len(product_urls)} potential product URLs")
            
            # Scrape each product
            products = []
            for url in product_urls:
                product = await self._extract_product_details(url)
                if product:
                    products.append(product)
                    
                # Respect rate limiting
                await asyncio.sleep(self.delay_between_requests)
            
            self.scraped_products = products
            self.logger.info(f"Successfully scraped {len(products)} ROCKWOOL products")
            
            return products
            
        except Exception as e:
            self.logger.error(f"Error in sitemap scraping: {e}")
            return []
    
    def save_to_json(self, filepath: str) -> bool:
        """
        Save scraped products to JSON file.
        
        Args:
            filepath: Path where to save the JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            products_data = [asdict(product) for product in self.scraped_products]
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(products_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Saved {len(products_data)} products to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving to JSON: {e}")
            return False


async def main():
    """Main function to run the scraper."""
    async with RockwoolScraper() as scraper:
        products = await scraper.scrape_products_from_sitemap()
        
        if products:
            # Save to JSON file
            output_file = "rockwool_products.json"
            scraper.save_to_json(output_file)
            
            print(f"✅ Successfully scraped {len(products)} ROCKWOOL products")
            print(f"📄 Data saved to: {output_file}")
            
            # Print sample product
            if products:
                sample = products[0]
                print(f"\n📋 Sample product: {sample.name}")
                print(f"   Category: {sample.category}")
                print(f"   Specs: {len(sample.technical_specs)} technical specifications")
        else:
            print("❌ No products were scraped")


if __name__ == "__main__":
    asyncio.run(main())