"""
ROCKWOOL PDF Scraper - Hungary Termékadatlapok
Scraping implementation for Lambda.hu PROS scope
"""
import logging
import os
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
from datetime import datetime
import httpx
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# ROCKWOOL Hungary Configuration
BASE_URL = "https://www.rockwool.com"
TERMEK_URL = (
    "https://www.rockwool.com/hu/muszaki-informaciok/termekadatlapok/"
)
API_URL = "https://www.rockwool.com/sitecore/api/rockwool/documentationlist/search"

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
        proxies = {"http://": self.proxy, "https://": self.proxy} if self.proxy else None
        self.session = httpx.AsyncClient(
            proxies=proxies,
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

    async def scrape_api(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Scrape ROCKWOOL Hungary termékadatlapok using their API
        """
        logger.info("🚀 ROCKWOOL SCRAPING STARTED...")

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

            logger.info(
                f"✅ Found {len(products)} termékadatlapok from API"
            )

            # Process each product
            processed_products = []
            for idx, product in enumerate(products[:limit] if limit else products):
                try:
                    processed_product = await self._process_product(
                        product, idx + 1
                    )
                    if processed_product:
                        processed_products.append(processed_product)

                except Exception as e:
                    logger.error(
                        f"❌ Error processing product {idx + 1}: {e}"
                    )
                    continue

            logger.info(
                f"🎯 Successfully processed {len(processed_products)} products"
            )
            return processed_products

        except Exception as e:
            logger.error(f"❌ Scraping failed: {e}")
            return []

    async def _process_product(
        self, product_data: Dict, index: int
    ) -> Optional[Dict]:
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

            # Get the actual product page to find PDFs
            if product_url:
                await self._scrape_product_page_for_pdfs(
                    product_info, product_url
                )

            return product_info

        except Exception as e:
            logger.error(f"❌ Product processing failed: {e}")
            return None

    async def _scrape_product_page_for_pdfs(
        self, product_info: Dict, product_url: str
    ):
        """Scrape the actual product page to find PDF download links"""
        try:
            logger.info(f"🔍 Scraping product page: {product_url}")
            response = await self.session.get(product_url)
            response.raise_for_status()

            html_content = response.text

            # Find PDF links in the HTML
            pdf_pattern = r'href=["\']([^"\']*\.pdf[^"\']*)["\']'
            pdf_matches = re.findall(
                pdf_pattern, html_content, re.IGNORECASE
            )

            # Also look for specific ROCKWOOL PDF patterns
            termek_pattern = (
                r'href=["\']([^"\']*termékadatlap[^"\']*\.pdf[^"\']*)["\']'
            )
            termek_matches = re.findall(
                termek_pattern, html_content, re.IGNORECASE
            )

            # Look for "Termékadatlap letöltése" or "Datenblatt herunterladen"
            download_pattern = (
                r'href=["\']([^"\']*)["\'][^>]*>[^<]*'
                r'(?:termékadatlap|letöltése|download|datenblatt)[^<]*</a>'
            )
            download_matches = re.findall(
                download_pattern, html_content, re.IGNORECASE
            )

            all_pdf_urls = list(set(
                pdf_matches + termek_matches + download_matches
            ))

            logger.info(
                f"📎 Found {len(all_pdf_urls)} potential PDF links"
            )

            for pdf_url in all_pdf_urls:
                if pdf_url.lower().endswith('.pdf'):
                    try:
                        pdf_result = await self._download_pdf(
                            pdf_url, product_info['name']
                        )
                        if pdf_result:
                            product_info['pdfs'].append(pdf_result)
                    except Exception as e:
                        logger.error(
                            f"❌ PDF download failed for {pdf_url}: {e}"
                        )

        except Exception as e:
            logger.error(
                f"❌ Failed to scrape product page {product_url}: {e}"
            )

    async def _download_pdf(
        self, pdf_url: str, product_name: str
    ) -> Optional[Dict]:
        """Download PDF"""
        try:
            if not pdf_url.startswith('http'):
                pdf_url = urljoin(BASE_URL, pdf_url)

            logger.info(f"⬇️ Downloading PDF: {pdf_url}")

            # Download PDF
            response = await self.session.get(pdf_url, follow_redirects=True)
            response.raise_for_status()

            # Check if it's actually a PDF
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower():
                logger.warning(f"⚠️ Not a PDF: {content_type}")
                return None

            # Generate filename
            safe_product_name = re.sub(r'[^\w\s-]', '', product_name)[:50]
            url_filename = os.path.basename(urlparse(pdf_url).path)
            if url_filename.endswith('.pdf'):
                filename = f"{safe_product_name}_{url_filename}"
            else:
                filename = f"{safe_product_name}_datasheet.pdf"

            filepath = PDF_STORAGE_DIR / filename

            # Save PDF
            with open(filepath, 'wb') as f:
                f.write(response.content)

            result = {
                'title': url_filename or 'Product Datasheet',
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
            logger.error(f"❌ PDF download failed: {e}")
            return None


async def scrape_rockwool(limit: Optional[int] = None) -> List[Dict]:
    """
    Scrape ROCKWOOL termékadatlapok and download PDFs
    """
    # Construct Bright Data proxy URL if credentials are available
    proxy = None
    api_token = os.getenv('BRIGHTDATA_API_TOKEN')
    zone = os.getenv('BRIGHTDATA_WEB_UNLOCKER_ZONE', 'web_unlocker')
    if api_token:
        proxy_user = f"brd-{api_token}"
        proxy_pass = api_token
        proxy_host = f"{zone}.brightdata.com"
        proxy_port = 22225
        proxy = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
        logger.info("Using Bright Data proxy for scraping.")
    else:
        logger.info("No Bright Data proxy configured. Scraping directly.")
        
    async with RockwoolScraper(proxy=proxy) as scraper:
        return await scraper.scrape_api(limit)


async def run_rockwool_scrape(limit: Optional[int] = 20) -> Dict:
    """
    Complete ROCKWOOL PDF scraping and storage
    """
    logger.info("🎯 Starting ROCKWOOL PDF scraping...")

    try:
        # Scrape products
        products = await scrape_rockwool(limit)

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