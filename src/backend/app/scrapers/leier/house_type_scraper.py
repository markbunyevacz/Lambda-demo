import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin

# --- Configuration ---
TIPUSHAZ_URL = "https://www.leier.hu/hu/tipushazak"
BASE_URL = "https://www.leier.hu"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """
    Fetches the main 'Típusházak' page and extracts links to individual house type pages.
    """
    logger.info(f"Starting Leier 'Típusházak' page analysis: {TIPUSHAZ_URL}")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(TIPUSHAZ_URL) as response:
                if response.status == 200:
                    soup = BeautifulSoup(await response.text(), 'html.parser')
                    
                    logger.info("--- Found House Type Links ---")
                    # This selector targets the specific cards for each house type
                    house_links = soup.select("a.leier-house-card")
                    
                    if not house_links:
                        logger.warning("No house type links found. The selector 'a.leier-house-card' may need an update.")
                    
                    for link in house_links:
                        href = link.get('href')
                        full_url = urljoin(BASE_URL, href)
                        title = link.select_one("h3").get_text(strip=True) if link.select_one("h3") else "No title"
                        logger.info(f"Title: {title} -> URL: {full_url}")
                        
                    logger.info("-----------------------------")
                else:
                    logger.error(f"Failed to fetch {TIPUSHAZ_URL}. Status: {response.status}")
        except Exception as e:
            logger.error(f"Error fetching or parsing page {TIPUSHAZ_URL}: {e}")

    logger.info("House type page analysis complete.")

if __name__ == "__main__":
    asyncio.run(main()) 