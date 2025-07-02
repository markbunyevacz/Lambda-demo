import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin

# --- Configuration ---
CALCULATOR_BASE_URL = "https://kalkulator.leier.hu/"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def analyze_calculator_page(session, url):
    """Fetches a specific calculator page and extracts its form data and links."""
    logger.info(f"Analyzing calculator page: {url}")
    try:
        async with session.get(url) as response:
            if response.status == 200:
                soup = BeautifulSoup(await response.text(), 'html.parser')

                # Find all forms and their inputs
                forms = soup.find_all('form')
                logger.info(f"Found {len(forms)} form(s) on the page.")
                for i, form in enumerate(forms):
                    logger.info(f"--- Form #{i+1} ---")
                    for input_tag in form.find_all(['input', 'select', 'textarea']):
                        name = input_tag.get('name')
                        input_type = input_tag.get('type', input_tag.name)
                        options = []
                        if input_tag.name == 'select':
                            options = [option.get_text(strip=True) for option in input_tag.find_all('option')]
                        logger.info(f"  Input: Name='{name}', Type='{input_type}', Options: {options if options else 'N/A'}")
                    logger.info("-" * 15)

            else:
                logger.error(f"Failed to fetch {url}. Status: {response.status}")
    except Exception as e:
        logger.error(f"Error analyzing page {url}: {e}")

async def main():
    """
    Main function to scrape and analyze a specific Leier calculator page.
    """
    target_url = "https://www.leier.hu/hoatbocsatasi-tenyezo-kalkulator-leieru"
    logger.info(f"Starting analysis of Leier U-value calculator: {target_url}")

    async with aiohttp.ClientSession() as session:
        await analyze_calculator_page(session, target_url)

    logger.info("Calculator page analysis complete.")

if __name__ == "__main__":
    asyncio.run(main()) 