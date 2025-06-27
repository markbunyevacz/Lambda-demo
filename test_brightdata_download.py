"""
Standalone BrightData PDF Download Test
Plan D: Isolate core functionality from application dependencies
"""
import asyncio
import logging
import sys
import httpx
import json
import os
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse
import re

# Add backend to path
sys.path.append('backend')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# PDF Storage Configuration
PDF_STORAGE_DIR = Path("downloads/brightdata_test")
PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class SimplePDFDownloader:
    """Simple PDF downloader without application dependencies"""
    
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/pdf,*/*',
            'Accept-Language': 'hu-HU,hu;q=0.9,en;q=0.8',
        }
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers=headers,
            follow_redirects=True
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    async def download_pdf(self, pdf_url: str, product_name: str) -> dict:
        """Download a single PDF"""
        try:
            logger.info(f"⬇️ Downloading: {pdf_url}")
            
            response = await self.session.get(pdf_url)
            response.raise_for_status()
            
            # Validate it's actually a PDF
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower():
                logger.warning(f"⚠️ Not a PDF: {content_type}")
                return {'status': 'failed', 'error': f'Not a PDF: {content_type}'}
            
            # Create safe filename
            safe_name = re.sub(r'[^\w\s-]', '', product_name)[:50]
            url_filename = os.path.basename(urlparse(pdf_url).path)
            if not url_filename.lower().endswith('.pdf'):
                url_filename = f"{safe_name}.pdf"
            
            filename = f"{safe_name}_{url_filename}"
            filepath = PDF_STORAGE_DIR / filename
            
            # Save the file
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            result = {
                'status': 'success',
                'filename': filename,
                'local_path': str(filepath),
                'file_size': len(response.content),
                'url': pdf_url,
                'content_type': content_type,
                'downloaded_at': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Downloaded: {filename} ({len(response.content)} bytes)")
            return result
            
        except Exception as e:
            logger.error(f"❌ Download failed for {product_name}: {e}")
            return {'status': 'failed', 'error': str(e), 'url': pdf_url}


async def test_brightdata_scraping():
    """Test BrightData agent for scraping"""
    logger.info("🚀 Testing BrightData Agent (Plan D)...")
    
    try:
        # Import the agent (this should work without psycopg2 dependencies)
        from app.agents.brightdata_agent import BrightDataMCPAgent
        
        # Initialize agent
        agent = BrightDataMCPAgent()
        if not agent.mcp_available:
            logger.error("❌ BrightData MCP Agent not available")
            return {'success': False, 'error': 'MCP Agent not available'}
        
        # Scrape the target URL
        target_url = "https://www.rockwool.com/hu/muszaki-informaciok/termekadatlapok/"
        logger.info(f"🎯 Scraping: {target_url}")
        
        products = await agent.scrape_rockwool_with_ai(target_urls=[target_url])
        
        logger.info(f"📊 Found {len(products)} products from AI scraping")
        
        # Filter products that have PDF URLs
        products_with_pdfs = [p for p in products if p.get('pdf_url')]
        logger.info(f"📄 Products with PDF URLs: {len(products_with_pdfs)}")
        
        return {
            'success': True,
            'total_products': len(products),
            'products_with_pdfs': len(products_with_pdfs),
            'products': products_with_pdfs
        }
        
    except Exception as e:
        logger.error(f"❌ BrightData scraping failed: {e}")
        return {'success': False, 'error': str(e)}


async def test_pdf_downloading(products_data):
    """Test PDF downloading for scraped products"""
    if not products_data['success']:
        logger.error("❌ Cannot test downloading - scraping failed")
        return {'success': False, 'downloads': []}
    
    products = products_data['products']
    if not products:
        logger.warning("⚠️ No products with PDFs to download")
        return {'success': True, 'downloads': []}
    
    logger.info(f"📥 Testing PDF downloads for {len(products)} products...")
    
    download_results = []
    
    async with SimplePDFDownloader() as downloader:
        for i, product in enumerate(products[:10]):  # Limit to first 10 for testing
            product_name = product.get('name', f'Product_{i+1}')
            pdf_url = product.get('pdf_url')
            
            if pdf_url:
                result = await downloader.download_pdf(pdf_url, product_name)
                download_results.append({
                    'product_name': product_name,
                    'pdf_url': pdf_url,
                    **result
                })
    
    successful_downloads = [r for r in download_results if r['status'] == 'success']
    failed_downloads = [r for r in download_results if r['status'] == 'failed']
    
    logger.info(f"✅ Successful downloads: {len(successful_downloads)}")
    logger.info(f"❌ Failed downloads: {len(failed_downloads)}")
    
    return {
        'success': True,
        'total_attempts': len(download_results),
        'successful_downloads': len(successful_downloads),
        'failed_downloads': len(failed_downloads),
        'downloads': download_results
    }


async def main():
    """Main test function for Plan D"""
    logger.info("🎯 Plan D: Standalone BrightData + PDF Download Test")
    
    # Step 1: Test BrightData scraping
    scraping_result = await test_brightdata_scraping()
    
    # Step 2: Test PDF downloading
    download_result = await test_pdf_downloading(scraping_result)
    
    # Step 3: Generate summary
    final_result = {
        'plan': 'D',
        'test_type': 'standalone_brightdata_pdf_test',
        'scraping': scraping_result,
        'downloading': download_result,
        'storage_location': str(PDF_STORAGE_DIR),
        'tested_at': datetime.now().isoformat()
    }
    
    # Save results
    results_file = 'plan_d_test_results.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📄 Results saved to: {results_file}")
    
    # Summary
    if scraping_result['success'] and download_result['success']:
        logger.info("🎉 Plan D SUCCESS: Core functionality proven!")
        logger.info(f"  - Products found: {scraping_result.get('total_products', 0)}")
        logger.info(f"  - PDFs downloaded: {download_result.get('successful_downloads', 0)}")
    else:
        logger.error("❌ Plan D FAILED: Core functionality issues detected")
    
    return final_result


if __name__ == "__main__":
    result = asyncio.run(main()) 