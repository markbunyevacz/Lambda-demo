"""
PRODUCTION ROCKWOOL PDF Scraper - Hungary Termékadatlapok
Real scraping implementation for Lambda.hu PROS scope
"""
import asyncio
import logging
import os
import hashlib
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
from datetime import datetime
import httpx
import fitz  # PyMuPDF
import re
from pathlib import Path
import json

logger = logging.getLogger(__name__)

# ROCKWOOL Hungary Configuration
BASE_URL = "https://www.rockwool.com"
TERMEK_URL = "https://www.rockwool.com/hu/muszaki-informaciok/termekadatlapok/"
API_URL = "https://www.rockwool.com/sitecore/api/rockwool/documentationlist/search"

# PDF Storage Configuration
PDF_STORAGE_DIR = Path("data/pdfs/rockwool")
PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

class ROCKWOOLProductionScraper:
    """Production-ready ROCKWOOL termékadatlapok scraper"""
    
    def __init__(self):
        self.session = None
        self.scraped_products = []
        
    async def __aenter__(self):
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'hu-HU,hu;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()

    async def scrape_termekadatlapok_api(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Scrape ROCKWOOL Hungary termékadatlapok using their API
        """
        logger.info("🚀 Starting PRODUCTION ROCKWOOL termékadatlapok scraping...")
        
        # API payload for Hungarian termékadatlapok
        payload = {
            "page": 1,
            "pageSize": limit or 50,
            "sort": "title-asc",
            "language": "hu",
            "filters": [
                {
                    "name": "documentation-category",
                    "value": "Termékadatlapok"
                }
            ]
        }
        
        try:
            logger.info(f"📡 Calling ROCKWOOL API: {API_URL}")
            response = await self.session.post(API_URL, json=payload)
            response.raise_for_status()
            
            data = response.json()
            products = data.get('results', [])
            
            logger.info(f"✅ Found {len(products)} termékadatlapok from API")
            
            # Process each product
            processed_products = []
            for idx, product in enumerate(products[:limit] if limit else products):
                try:
                    processed_product = await self._process_product(product, idx + 1)
                    if processed_product:
                        processed_products.append(processed_product)
                        
                except Exception as e:
                    logger.error(f"❌ Error processing product {idx + 1}: {e}")
                    continue
                    
            logger.info(f"🎯 Successfully processed {len(processed_products)} products")
            return processed_products
            
        except Exception as e:
            logger.error(f"❌ API scraping failed: {e}")
            return []

    async def _process_product(self, product_data: Dict, index: int) -> Optional[Dict]:
        """Process individual product and download PDFs"""
        try:
            product_name = product_data.get('title', f'Product_{index}')
            product_url = product_data.get('url', '')
            
            if product_url and not product_url.startswith('http'):
                product_url = urljoin(BASE_URL, product_url)
                
            logger.info(f"📄 Processing #{index}: {product_name}")
            
            # Extract product details
            product_info = {
                'name': product_name,
                'url': product_url,
                'description': product_data.get('description', ''),
                'category': 'Termékadatlapok',
                'language': 'hu',
                'scraped_at': datetime.now().isoformat(),
                'pdfs': []
            }
            
            # Look for PDF downloads in the product data
            pdf_links = self._extract_pdf_links(product_data)
            
            for pdf_info in pdf_links:
                try:
                    pdf_result = await self._download_pdf(pdf_info, product_name)
                    if pdf_result:
                        product_info['pdfs'].append(pdf_result)
                except Exception as e:
                    logger.error(f"❌ PDF download failed for {pdf_info.get('url', 'unknown')}: {e}")
                    
            return product_info
            
        except Exception as e:
            logger.error(f"❌ Product processing failed: {e}")
            return None
            
    def _extract_pdf_links(self, product_data: Dict) -> List[Dict]:
        """Extract PDF download links from product data"""
        pdf_links = []
        
        # Check for direct PDF URLs
        attachments = product_data.get('attachments', [])
        for attachment in attachments:
            if attachment.get('url', '').lower().endswith('.pdf'):
                pdf_links.append({
                    'url': attachment['url'],
                    'title': attachment.get('title', 'Product PDF'),
                    'type': 'datasheet'
                })
                
        # Check for documentation links
        documents = product_data.get('documents', [])
        for doc in documents:
            if doc.get('url', '').lower().endswith('.pdf'):
                pdf_links.append({
                    'url': doc['url'],
                    'title': doc.get('title', 'Technical Document'),
                    'type': 'technical'
                })
                
        return pdf_links
        
    async def _download_pdf(self, pdf_info: Dict, product_name: str) -> Optional[Dict]:
        """Download and process individual PDF"""
        try:
            pdf_url = pdf_info['url']
            if not pdf_url.startswith('http'):
                pdf_url = urljoin(BASE_URL, pdf_url)
                
            logger.info(f"⬇️ Downloading PDF: {pdf_info['title']}")
            
            # Download PDF
            response = await self.session.get(pdf_url)
            response.raise_for_status()
            
            # Generate filename
            safe_product_name = re.sub(r'[^\w\s-]', '', product_name)[:50]
            safe_title = re.sub(r'[^\w\s-]', '', pdf_info['title'])[:30]
            filename = f"{safe_product_name}_{safe_title}.pdf"
            filepath = PDF_STORAGE_DIR / filename
            
            # Save PDF
            with open(filepath, 'wb') as f:
                f.write(response.content)
                
            # Extract PDF metadata and content
            pdf_metadata = await self._extract_pdf_content(filepath)
            
            result = {
                'title': pdf_info['title'],
                'url': pdf_url,
                'local_path': str(filepath),
                'filename': filename,
                'file_size': len(response.content),
                'type': pdf_info.get('type', 'unknown'),
                'downloaded_at': datetime.now().isoformat(),
                **pdf_metadata
            }
            
            logger.info(f"✅ Downloaded: {filename} ({len(response.content)} bytes)")
            return result
            
        except Exception as e:
            logger.error(f"❌ PDF download failed: {e}")
            return None
            
    async def _extract_pdf_content(self, filepath: Path) -> Dict:
        """Extract content and metadata from PDF"""
        try:
            doc = fitz.open(filepath)
            
            # Extract metadata
            metadata = doc.metadata
            
            # Extract text content from first few pages
            content_pages = []
            for page_num in range(min(3, len(doc))):  # First 3 pages
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    content_pages.append(text.strip())
                    
            doc.close()
            
            # Look for technical specifications
            full_text = ' '.join(content_pages)
            specs = self._extract_technical_specs(full_text)
            
            return {
                'pdf_metadata': {
                    'title': metadata.get('title', ''),
                    'author': metadata.get('author', ''),
                    'creator': metadata.get('creator', ''),
                    'pages': len(doc)
                },
                'extracted_content': content_pages,
                'technical_specs': specs
            }
            
        except Exception as e:
            logger.error(f"❌ PDF content extraction failed: {e}")
            return {}
            
    def _extract_technical_specs(self, text: str) -> Dict:
        """Extract technical specifications from PDF text"""
        specs = {}
        
        # Common ROCKWOOL specifications
        patterns = {
            'r_value': r'R[- ]?értéke?:?\s*(\d+(?:,\d+)?)',
            'lambda_value': r'λ[D]?\s*[≤=]\s*(\d+,\d+)',
            'thickness': r'Vastagság.*?(\d+)\s*mm',
            'density': r'sűrűség.*?(\d+)\s*kg/m',
            'thermal_conductivity': r'hővezetési.*?(\d+,\d+)',
            'fire_class': r'Tűzvédelmi.*?(A\d+)',
            'melting_point': r'Olvadáspont.*?(\d+).*?°C'
        }
        
        for spec_name, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                specs[spec_name] = match.group(1)
                
        return specs

# Main scraping functions for integration
async def scrape_rockwool_production(limit: Optional[int] = None) -> List[Dict]:
    """
    PRODUCTION function - Scrape ROCKWOOL termékadatlapok
    """
    async with ROCKWOOLProductionScraper() as scraper:
        return await scraper.scrape_termekadatlapok_api(limit)

async def scrape_and_store_rockwool_pdfs(limit: Optional[int] = 20) -> Dict:
    """
    Complete ROCKWOOL PDF scraping and storage for Lambda.hu database
    """
    logger.info("🎯 Starting ROCKWOOL PDF scraping for PROS scope...")
    
    try:
        # Scrape products
        products = await scrape_rockwool_production(limit)
        
        # Summary statistics
        total_products = len(products)
        total_pdfs = sum(len(p.get('pdfs', [])) for p in products)
        
        result = {
            'success': True,
            'products_scraped': total_products,
            'pdfs_downloaded': total_pdfs,
            'products': products,
            'storage_location': str(PDF_STORAGE_DIR),
            'scraped_at': datetime.now().isoformat()
        }
        
        logger.info(f"🎉 ROCKWOOL scraping completed: {total_products} products, {total_pdfs} PDFs")
        return result
        
    except Exception as e:
        logger.error(f"❌ ROCKWOOL scraping failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'products_scraped': 0,
            'pdfs_downloaded': 0
        }

# Legacy compatibility
async def scrape_rockwool_for_database(limit: Optional[int] = None) -> List[Dict]:
    """Legacy function for existing integrations"""
    return await scrape_rockwool_production(limit)