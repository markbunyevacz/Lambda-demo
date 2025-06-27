"""
ROCKWOOL PDF Scraper - Hungary Termékadatlapok
Scraping implementation for Lambda.hu PROS scope
"""
import logging
import os
import json
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
from datetime import datetime
import httpx
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# ROCKWOOL Hungary Configuration
BASE_URL = "https://www.rockwool.com"
TERMEK_URL = "https://www.rockwool.com/hu/muszaki-informaciok/termekadatlapok/"

# PDF Storage Configuration
PDF_STORAGE_DIR = Path("data/scraped_pdfs/rockwool")
PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class RockwoolScraper:
    """ROCKWOOL termékadatlapok scraper"""

    def __init__(self, proxy: Optional[str] = None):
        self.session: Optional[httpx.AsyncClient] = None
        self.scraped_products: list = []
        self.proxy = proxy

    async def __aenter__(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'hu-HU,hu;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.session = httpx.AsyncClient(
            proxy=self.proxy,
            timeout=30.0,
            headers=headers,
            follow_redirects=True
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()

    async def scrape_page_for_pdfs(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Scrape ROCKWOOL Hungary termékadatlapok by parsing the page HTML.
        """
        logger.info("🚀 ROCKWOOL SCRAPING STARTED (HTML Parsing Method)...")

        try:
            logger.info(f"📡 Fetching page: {TERMEK_URL}")
            if not self.session:
                raise ConnectionError("Session not initialized.")
            response = await self.session.get(TERMEK_URL)
            response.raise_for_status()
            html_content = response.text

            # The data is in a malformed JSON inside a data-component-props attribute
            props_pattern = r'data-component-props="({.*})"'
            props_match = re.search(props_pattern, html_content, re.DOTALL)
            if not props_match:
                logger.error("Could not find data-component-props attribute.")
                return []

            props_str = props_match.group(1).replace('&quot;', '"')
            
            # Clean up known malformations in the JSON string
            # This is a more robust way to find the end of the JSON object
            # by balancing curly braces, instead of fragile regex replacements.
            open_braces = 0
            end_index = -1
            for i, char in enumerate(props_str):
                if char == '{':
                    open_braces += 1
                elif char == '}':
                    open_braces -= 1
                    if open_braces == 0:
                        end_index = i + 1
                        break
            
            if end_index == -1:
                logger.error("Could not determine the end of the JSON object.")
                return []

            fixed_props_str = props_str[:end_index]

            props_data = json.loads(fixed_props_str)
            download_list = props_data.get('downloadList', [])

            logger.info(f"✅ Found {len(download_list)} PDFs from page HTML")

            processed_products = []
            for idx, item in enumerate(download_list[:limit] if limit else download_list):
                try:
                    product_info = {
                        'name': item.get('title', f'Product_{idx + 1}'),
                        'url': item.get('fileUrl', ''),
                        'description': item.get('description', ''),
                        'category': item.get('category', 'Unknown').split('*')[-1],
                        'language': 'hu',
                        'scraped_at': datetime.now().isoformat(),
                        'pdfs': []
                    }

                    pdf_url = item.get('fileUrl')
                    if pdf_url:
                        pdf_result = await self._download_pdf(pdf_url, product_info['name'])
                        if pdf_result:
                            product_info['pdfs'].append(pdf_result)
                    
                    processed_products.append(product_info)
                except Exception as e:
                    logger.error(f"❌ Error processing product {item.get('title', 'Unknown')}: {e}")
                    continue

            logger.info(f"🎯 Successfully processed {len(processed_products)} products")
            return processed_products

        except Exception as e:
            logger.error(f"❌ Scraping failed: {e}", exc_info=True)
            return []

    async def _download_pdf(
        self, pdf_url: str, product_name: str
    ) -> Optional[Dict]:
        """Download PDF"""
        try:
            if not pdf_url.startswith('http'):
                pdf_url = urljoin(BASE_URL, pdf_url)

            logger.info(f"⬇️ Downloading PDF: {pdf_url}")

            if not self.session:
                raise ConnectionError("Session not initialized.")
            response = await self.session.get(pdf_url, follow_redirects=True)
            response.raise_for_status()

            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower():
                logger.warning(f"⚠️ Not a PDF: {content_type} for URL {pdf_url}")
                return None

            safe_product_name = re.sub(r'[^\w\s-]', '', product_name)[:50]
            url_filename = os.path.basename(urlparse(pdf_url).path)
            if not url_filename.lower().endswith('.pdf'):
                url_filename = f"{safe_product_name}.pdf"

            filename = f"{safe_product_name}_{url_filename}"
            filepath = PDF_STORAGE_DIR / filename

            with open(filepath, 'wb') as f:
                f.write(response.content)

            result = {
                'title': url_filename,
                'url': pdf_url,
                'local_path': str(filepath),
                'filename': filename,
                'file_size': len(response.content),
                'content_type': content_type,
                'downloaded_at': datetime.now().isoformat(),
                'status': 'success'
            }

            logger.info(
                f"✅ Downloaded {filename} ({len(response.content)} bytes)"
            )
            return result

        except Exception as e:
            logger.error(f"❌ PDF download failed for {product_name}: {e}")
            return None


async def scrape_rockwool(limit: Optional[int] = None) -> List[Dict]:
    """
    Scrape ROCKWOOL termékadatlapok and download PDFs
    """
    proxy = None
    api_token = os.getenv('BRIGHTDATA_API_TOKEN')
    customer_id = os.getenv('BRIGHTDATA_CUSTOMER_ID')
    zone = os.getenv('BRIGHTDATA_WEB_UNLOCKER_ZONE', 'web_unlocker')

    if api_token and customer_id:
        proxy_user = f"brd-customer-{customer_id}-zone-{zone}"
        proxy_pass = api_token
        proxy_host = "brd.superproxy.io"
        proxy_port = 22225
        proxy = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
        logger.info("Using Bright Data proxy for scraping.")
    else:
        logger.info("Bright Data credentials not fully configured. Scraping directly.")
        logger.info("Please set BRIGHTDATA_API_TOKEN and BRIGHTDATA_CUSTOMER_ID in your .env file.")

    async with RockwoolScraper(proxy=proxy) as scraper:
        return await scraper.scrape_page_for_pdfs(limit)


async def run_rockwool_scrape(limit: Optional[int] = 20) -> Dict:
    """
    Complete ROCKWOOL PDF scraping and storage
    """
    logger.info("🎯 Starting ROCKWOOL PDF scraping...")

    try:
        products = await scrape_rockwool(limit)

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

        logger.info(
            f"🎉 COMPLETE: {total_products} products, "
            f"{total_pdfs} PDFs downloaded"
        )
        return result

    except Exception as e:
        logger.error(f"❌ Scraping run failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'products_scraped': 0,
            'pdfs_downloaded': 0
        }