"""
PDF Download Test Script
Testing the current Rockwool PDF downloading infrastructure
"""
import asyncio
import logging
import sys

# Add backend to path
sys.path.append('backend')

from app.scrapers.rockwool import RockwoolScraper, scrape_rockwool  # noqa

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_pdf_download():
    """Test the current PDF downloading functionality"""
    logger.info("🧪 Testing PDF Download Infrastructure...")
    
    try:
        # Test with a small limit first
        logger.info("📊 Testing with 5 products first...")
        result = await scrape_rockwool(limit=5)
        
        logger.info(f"📈 Test Results:")
        logger.info(f"  - Products found: {len(result)}")
        
        successful_downloads = []
        failed_downloads = []
        
        for product in result:
            if product.get('pdfs'):
                for pdf in product['pdfs']:
                    if pdf.get('status') == 'success':
                        successful_downloads.append(pdf)
                    else:
                        failed_downloads.append(pdf)
            else:
                failed_downloads.append({
                    'product_name': product.get('name'),
                    'url': product.get('url'),
                    'error': 'No PDFs downloaded'
                })
        
        logger.info(f"✅ Successful downloads: {len(successful_downloads)}")
        logger.info(f"❌ Failed downloads: {len(failed_downloads)}")
        
        # Show details of successful downloads
        if successful_downloads:
            logger.info("🎯 Successful Downloads:")
            for pdf in successful_downloads:
                logger.info(f"  - {pdf['filename']} ({pdf['file_size']} bytes)")
                logger.info(f"    URL: {pdf['url']}")
                logger.info(f"    Path: {pdf['local_path']}")
        
        # Show details of failed downloads (first 3)
        if failed_downloads:
            logger.info("❌ Failed Downloads (first 3):")
            for pdf in failed_downloads[:3]:
                if 'product_name' in pdf:
                    logger.info(f"  - {pdf['product_name']}")
                    logger.info(f"    URL: {pdf.get('url', 'N/A')}")
                    logger.info(f"    Error: {pdf.get('error', 'Unknown')}")
        
        return {
            'total_products': len(result),
            'successful_downloads': len(successful_downloads),
            'failed_downloads': len(failed_downloads),
            'products': result
        }
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return {
            'error': str(e),
            'total_products': 0,
            'successful_downloads': 0,
            'failed_downloads': 0
        }

async def test_specific_urls():
    """Test specific PDF URLs to understand the 404 issues"""
    logger.info("🔍 Testing specific PDF URLs...")
    
    # Test URLs from the metadata that failed
    test_urls = [
        "https://p-cdn.rockwool.com/syssiteassets/rw-hu/termekadatlapok/laposteto/monrock-max-e.pdf",
        "https://p-cdn.rockwool.com/syssiteassets/rw-hu/termekadatlapok/laposteto/rockfall.pdf",
        "https://p-cdn.rockwool.com/syssiteassets/rw-hu/termekadatlapok/gepeszet/klimamat-040.pdf"
    ]
    
    async with RockwoolScraper() as scraper:
        for url in test_urls:
            try:
                logger.info(f"🔍 Testing URL: {url}")
                result = await scraper._download_pdf(url, f"Test_{url.split('/')[-1]}")
                if result:
                    logger.info(f"✅ Success: {result['filename']}")
                else:
                    logger.info(f"❌ Failed: No result returned")
            except Exception as e:
                logger.error(f"❌ Error for {url}: {e}")

async def main():
    """Main test function"""
    logger.info("🚀 Starting PDF Download Testing...")
    
    # Test current infrastructure
    test_result = await test_pdf_download()
    
    # Test specific URLs
    await test_specific_urls()
    
    # Summary
    logger.info("📋 Test Summary:")
    logger.info(f"  Total products: {test_result.get('total_products', 0)}")
    logger.info(f"  Successful downloads: {test_result.get('successful_downloads', 0)}")
    logger.info(f"  Failed downloads: {test_result.get('failed_downloads', 0)}")
    
    if test_result.get('error'):
        logger.error(f"  Error: {test_result['error']}")
    
    return test_result

if __name__ == "__main__":
    result = asyncio.run(main()) 