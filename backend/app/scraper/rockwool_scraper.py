# This file is intentionally left blank before pasting the new API-based scraper code.

"""
Rockwool Scraper - API-alapú, célzott adatgyűjtés PDF-ekből
"""
import asyncio
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin
import httpx
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# A Rockwool belső API végpontja
API_URL = "https://www.rockwool.com/sitecore/api/rockwool/documentationlist/search"
BASE_URL = "https://www.rockwool.com/"

# A POST kéréshez szükséges payload. Ez a "Termékadatlapok" kategóriára szűr.
API_PAYLOAD = {
    "page": 1,
    "pageSize": 100,  # Kérjünk le egyszerre sok találatot
    "sort": "title-asc",
    "language": "hu",
    "filters": [{
        "name": "documentation-category",
        "value": "Termékadatlapok"
    }]
}


class RockwoolApiScraper:
    """
    Rockwool adatgyűjtő, ami a hivatalos belső API-t használja 
    a PDF termékadatlapok listájának és tartalmának kinyerésére.
    """
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.failed_urls = []

    async def _get_pdf_list_from_api(self) -> List[Dict[str, str]]:
        """
        Lekéri a termékadatlapok listáját a Rockwool API-n keresztül.
        """
        logger.info(f"Terméklista lekérése a Rockwool API-ról: {API_URL}")
        product_list = []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(API_URL, json=API_PAYLOAD, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()

                if data and data.get("results"):
                    for item in data["results"]:
                        # Az URL gyakran relatív, ezért teljes URL-t képzünk
                        pdf_url = urljoin(BASE_URL, item.get("url", ""))
                        product_list.append({
                            "name": item.get("title", "Ismeretlen termék"),
                            "url": pdf_url
                        })
                    logger.info(f"Sikeresen lekérve {len(product_list)} termékadatlap információ.")
                else:
                    logger.warning("Az API válasz nem tartalmazott 'results' kulcsot vagy üres volt.")

        except httpx.RequestError as e:
            logger.error(f"Hiba a Rockwool API hívása közben: {e}")
        
        return product_list

    async def _scrape_pdf_content(self, pdf_info: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Letölt egy PDF-et, és kinyeri a teljes szöveges tartalmát."""
        pdf_url = pdf_info["url"]
        logger.info(f"PDF feldolgozása: {pdf_info['name']} ({pdf_url})")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(pdf_url, timeout=self.timeout)
                response.raise_for_status()
                pdf_body = response.content

            if not pdf_body:
                logger.warning(f"A PDF letöltése üres tartalommal tért vissza: {pdf_url}")
                return None
            
            doc = fitz.open(stream=pdf_body, filetype="pdf")
            full_text = ""
            for page in doc:
                full_text += page.get_text() + "\n"
            
            return {
                "name": pdf_info['name'],
                "url": pdf_url,
                "full_text_content": full_text
            }
        except Exception as e:
            logger.error(f"Hiba a PDF feldolgozása során {pdf_url}: {e}")
            self.failed_urls.append(pdf_url)
            return None

    async def scrape_all_product_datasheets(self, limit: int = None) -> List[Dict[str, str]]:
        """
        A fő DEMO scraper funkció. Lekéri és feldolgozza a PDF termékadatlapokat.
        """
        pdf_infos = await self._get_pdf_list_from_api()
        if not pdf_infos:
            return []

        if limit:
            pdf_infos = pdf_infos[:limit]
            logger.info(f"Limitálva az első {limit} PDF feldolgozására a DEMO számára.")

        tasks = [self._scrape_pdf_content(info) for info in pdf_infos]
        all_products_raw = await asyncio.gather(*tasks)
        
        # Kiszűrjük a sikertelenül feldolgozott (None) elemeket
        all_products = [p for p in all_products_raw if p is not None]
        
        logger.info(f"PDF Scraping befejezve. Összesen {len(all_products)} termék sikeresen feldolgozva.")
        return all_products