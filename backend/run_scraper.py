"""
Unified Scraper Runner for Lambda.hu PROS Scope
"""
import asyncio
import argparse
import logging
from dotenv import load_dotenv
import json
import sys
from pathlib import Path
from datetime import datetime

# Add the backend directory to the Python path to resolve app.* imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ScraperRunner')

# --- Scraper Imports ---
# Import your scraper functions here as they are created
from app.scrapers.rockwool import run_rockwool_scrape
# Direct import to avoid database dependencies
from app.agents.brightdata_agent import BrightDataMCPAgent
# from app.scrapers.another_site import run_another_site_scrape

from app.scrapers.rockwool import RockwoolScraper


async def main():
    """
    Main function to run scrapers based on command line arguments
    """
    parser = argparse.ArgumentParser(description="Run web scrapers for Lambda.hu")
    parser.add_argument('scraper', type=str, help="The scraper to run (e.g., 'rockwool')")
    parser.add_argument('--limit', type=int, default=None, help="Limit the number of products to scrape")
    args = parser.parse_args()

    if args.scraper == 'rockwool':
        logger.info("Running Rockwool scraper with BrightData AI Agent...")
        agent = BrightDataMCPAgent()
        if not agent.mcp_available:
            logger.error("BrightData MCP Agent is not available. Check .env configuration.")
            result = {'success': False, 'error': 'BrightData MCP Agent not available.'}
        else:
            target_url = "https://www.rockwool.com/hu/muszaki-informaciok/termekadatlapok/"
            logger.info(f"AI Agent targeting URL: {target_url}")
            products = await agent.scrape_rockwool_with_ai(target_urls=[target_url])
            
            # Now, download the PDFs found by the AI
            async with RockwoolScraper() as downloader:
                for product in products:
                    if product.get('pdf_url'):
                        pdf_result = await downloader._download_pdf(product['pdf_url'], product['name'])
                        if pdf_result:
                            product.setdefault('pdfs', []).append(pdf_result)

            result = {
                'success': True,
                'products_scraped': len(products),
                'pdfs_downloaded': sum(len(p.get('pdfs', [])) for p in products),
                'products': products,
                'storage_location': 'data/scraped_pdfs/rockwool',
                'scraped_at': datetime.now().isoformat()
            }
    # Add other scrapers here with 'elif'
    # elif args.scraper == 'another_site':
    #     result = await run_another_site_scrape(limit=args.limit)

    else:
        logger.error(f"Unknown scraper: {args.scraper}")
        return

    # Save results to a file
    output_file = f"{args.scraper}_prod_run.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(f"Results saved to {output_file}")


if __name__ == "__main__":
    # To run: python backend/run_scraper.py rockwool-ai
    asyncio.run(main()) 