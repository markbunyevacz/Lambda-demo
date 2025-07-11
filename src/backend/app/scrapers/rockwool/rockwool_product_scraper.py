"""
Rockwool Product Scraper (Direct Method)
----------------------------------------

This script scrapes Rockwool product datasheets using a direct,
reliable method by parsing a JSON data block embedded in the page's HTML.
It replaces the previous, unreliable AI-based scraper.

Key Features:
- Fetches HTML from the product datasheets page.
- Extracts a hidden JSON block containing all product data.
- Parses product information (name, category, PDF URL).
- Downloads all related PDF documents with robust duplicate handling.
"""
import asyncio
import logging
import json
import httpx
import re
import hashlib
import html
from pathlib import Path
from urllib.parse import urljoin

from app.utils import get_project_root

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = get_project_root()
PDF_STORAGE_DIR = PROJECT_ROOT / "downloads" / "rockwool_datasheets"
DUPLICATES_DIR = PDF_STORAGE_DIR / "duplicates"
# Use a path relative to the project root for consistency
DEBUG_FILE_PATH = PROJECT_ROOT / "rockwool_datasheet_page.html"

# Ensure directories exist
PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
DUPLICATES_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://www.rockwool.com"
DATASHEET_URL = (
    "https://www.rockwool.com/hu/muszaki-informaciok/termekadatlapok/"
)


def clean_filename(text: str) -> str:
    """
    Cleans a filename by decoding HTML entities and removing invalid characters.
    """
    # Decode HTML entities (&#xE9; -> é, etc.)
    decoded = html.unescape(text)
    # Remove or replace invalid filename characters
    # Keep Hungarian characters and basic punctuation
    cleaned = re.sub(r'[<>:"/\\|?*]', '', decoded)
    # Replace multiple spaces with single space and trim
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned[:60]  # Limit length


class RockwoolProductScraper:
    """
    Scrapes Rockwool product datasheets by parsing embedded JSON data.
    """

    def __init__(self):
        self.documents = []
        self.downloaded_files = set()
        self.duplicate_count = 0
        self.successful_downloads = 0
        self.failed_downloads = 0

    async def fetch_page_content(self) -> str:
        """
        Fetches live page content from the Rockwool website.
        NO FALLBACK - always uses fresh, live data.
        """
        logger.info("🌐 Fetching LIVE page content from Rockwool website...")
        
        try:
            async with httpx.AsyncClient(
                timeout=30.0, follow_redirects=True
            ) as client:
                response = await client.get(DATASHEET_URL)
                response.raise_for_status()
                logger.info("✅ Successfully fetched LIVE page content!")
                
                # Optional: Save current content for debugging purposes only
                # (but never use it as fallback)
                try:
                    with open(DEBUG_FILE_PATH, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    logger.info(f"📄 Debug copy saved to: {DEBUG_FILE_PATH}")
                except Exception as save_error:
                    logger.warning(
                        f"⚠️  Could not save debug copy: {save_error}"
                    )
                
                return response.text
                
        except Exception as e:
            logger.error(f"❌ LIVE fetch failed: {e}")
            logger.error(
                "🚫 NO FALLBACK AVAILABLE - Cannot proceed without live data"
            )
            raise Exception(
                f"Failed to fetch live data from {DATASHEET_URL}: {e}"
            )

    def parse_products_from_html(self, html_content: str):
        """
        Parses product data from the O74DocumentationList JSON block
        in the HTML.
        """
        if not html_content:
            logger.error("HTML content is empty, cannot parse.")
            return

        props_pattern = (
            r'data-component-name="O74DocumentationList"[^>]*'
            r'data-component-props="({.*?})"'
        )
        props_match = re.search(props_pattern, html_content, re.DOTALL)

        if not props_match:
            logger.error(
                "Could not find O74DocumentationList component data in HTML."
            )
            return

        try:
            # The regex captures the JSON string. It needs to be unescaped.
            props_str = props_match.group(1).replace('&quot;', '"')

            # This is a complex nested JSON, we need to handle it carefully
            # A simple json.loads might fail if the outer layer is not perfect
            json_data = json.loads(props_str)

            product_list = json_data.get('downloadList', [])
            logger.info(
                f"Found {len(product_list)} product entries in JSON data."
            )

            for item in product_list:
                # The actual PDF URL is nested inside another JSON string
                # in the 'jsonDataObject'
                json_data_obj_str = item.get('jsonDataObject', '{}')
                json_data_obj = json.loads(json_data_obj_str)

                # The first file in the list is usually the main PDF
                file_info = json_data_obj.get('fileTypes', [{}])[0]
                pdf_url = file_info.get('url')

                if pdf_url:
                    self.documents.append({
                        "name": item.get("title", "Unnamed Product"),
                        "category": item.get("category", "Uncategorized"),
                        "pdf_url": urljoin(BASE_URL, pdf_url)
                    })

            logger.info(
                f"Successfully parsed {len(self.documents)} documents."
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON data: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during parsing: {e}")

    async def download_all_pdfs(self):
        """
        Downloads all discovered PDFs with duplicate handling.
        """
        if not self.documents:
            logger.warning("No documents to download.")
            return

        logger.info(
            f"Starting download of {len(self.documents)} "
            "product datasheets..."
        )

        async with httpx.AsyncClient(
            timeout=60.0, follow_redirects=True
        ) as session:
            tasks = [self._download_pdf(session, doc) for doc in self.documents]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for res in results:
                if isinstance(res, dict) and res.get('status') == 'success':
                    self.successful_downloads += 1
                else:
                    self.failed_downloads += 1

    def _generate_unique_filename(
            self, base_filename: str, pdf_url: str
    ) -> str:
        """Generates a unique filename to avoid collisions."""
        name_part, extension = Path(base_filename).stem, Path(base_filename).suffix
        url_hash = hashlib.md5(pdf_url.encode()).hexdigest()[:8]
        return f"{name_part}_{url_hash}{extension}"

    async def _download_pdf(self, session: httpx.AsyncClient, doc: dict):
        """Downloads a single PDF document."""
        pdf_url = doc['pdf_url']
        safe_name = clean_filename(doc['name'])
        base_filename = f"{safe_name}.pdf"

        # Check if filename already exists in our tracking set
        if base_filename in self.downloaded_files:
            # This is a duplicate - generate name and save to duplicates
            unique_filename = self._generate_unique_filename(
                base_filename, pdf_url
            )
            filepath = DUPLICATES_DIR / unique_filename
            self.duplicate_count += 1
            logger.info(
                f"Duplicate filename: {base_filename}. "
                f"Saving to duplicates as {unique_filename}"
            )
        else:
            # First occurrence - save to main directory
            filepath = PDF_STORAGE_DIR / base_filename
            self.downloaded_files.add(base_filename)

        logger.info(f"Downloading: {doc['name']} from {pdf_url}")
        try:
            response = await session.get(pdf_url)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                f.write(response.content)

            return {'status': 'success', 'path': str(filepath)}
        except Exception as e:
            logger.error(f"Failed to download {doc['name']}: {e}")
            return {'status': 'failed', 'name': doc['name'], 'error': str(e)}

    def _log_summary(self):
        """Logs the final summary of the scraping process."""
        logger.info("=" * 60)
        logger.info("ROCKWOOL PRODUCT SCRAPER - FINAL SUMMARY")
        logger.info("=" * 60)
        logger.info(f"📄 Documents Parsed: {len(self.documents)}")
        logger.info(f"✅ Successful Downloads: {self.successful_downloads}")
        logger.info(f"❌ Failed Downloads: {self.failed_downloads}")
        logger.info(f"🔄 Duplicates Found: {self.duplicate_count}")
        logger.info(f"📂 Main Storage: {PDF_STORAGE_DIR.resolve()}")
        if self.duplicate_count > 0:
            logger.info(f"📂 Duplicates Storage: {DUPLICATES_DIR.resolve()}")
        logger.info("=" * 60)

    async def run(self):
        """Main execution flow for the scraper."""
        logger.info(
            "--- Starting Rockwool Product Scraper (Direct Method) ---"
        )
        html_content = await self.fetch_page_content()
        self.parse_products_from_html(html_content)
        await self.download_all_pdfs()
        self._log_summary()
        
        # Save state after successful scraping
        await self.save_scraping_state()
        
        logger.info("--- Rockwool Product Scraper Finished ---")

    async def save_scraping_state(self):
        """Save current scraping state using RockwoolStateManager"""
        try:
            from .rockwool_state_manager import save_current_rockwool_state
            
            # Prepare products data for state manager
            products_data = []
            for doc in self.documents:
                # Find corresponding file info from downloads
                file_info = None
                for downloaded_file in self.downloaded_files:
                    if doc['name'] in downloaded_file:
                        file_info = downloaded_file
                        break
                
                product_data = {
                    'name': doc['name'],
                    'category': doc.get('category', 'Termékadatlapok'),
                    'pdf_url': doc['pdf_url'],
                    'file_path': file_info,
                    'file_size_bytes': None,  # Could be enhanced to get actual size
                    'is_duplicate': False  # Will be determined by state manager
                }
                products_data.append(product_data)
            
            # Add statistics
            statistics = {
                'total_products': len(self.documents),
                'successful_downloads': self.successful_downloads,
                'failed_downloads': self.failed_downloads,
                'duplicates_found': self.duplicate_count,
                'scraper_type': 'product_datasheets'
            }
            
            # Add config
            config = {
                'scraper_type': 'live_data',
                'data_source': 'rockwool.com/termekadatlapok',
                'language': 'hu',
                'fallback_used': False,
                'datasheet_url': DATASHEET_URL,
            }
            
            # Save state in all formats
            saved_files = await save_current_rockwool_state(
                products_data, 
                statistics=statistics, 
                config=config
            )
            
            logger.info("💾 Scraping állapot elmentve:")
            for format_type, filepath in saved_files.items():
                logger.info(f"   {format_type.upper()}: {filepath}")
                
        except Exception as e:
            logger.warning(f"⚠️  Állapot mentés sikertelen: {e}")


async def main():
    """Standalone runner function."""
    scraper = RockwoolProductScraper()
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main()) 