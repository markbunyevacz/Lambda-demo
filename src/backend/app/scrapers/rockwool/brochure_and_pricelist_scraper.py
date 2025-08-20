"""
Rockwool Brochure and Pricelist Scraper
---------------------------------------

Purpose:
This script is responsible for downloading all supplementary documents,
such as marketing brochures, official pricelists, and installation guides,
from the Rockwool Hungary website. It complements the datasheet scraper.

Key Features:
- Targets the "Pricelists and Brochures" section of the website.
- Uses a direct HTML parsing method on content fetched via BrightData.
- Fully asynchronous downloads for high performance.

This is a final, production-ready version.
"""
import asyncio
import logging
import json
import httpx
import re
import hashlib
import html
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin


# --- Configuration ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# PERMANENT FIX: Use absolute path from project root
PROJECT_ROOT = Path(__file__).resolve().parents[5]  # Go up to Lambda/ root
PDF_STORAGE_DIR = PROJECT_ROOT / "src" / "backend" / "src" / "downloads" / "rockwool_datasheets"
DUPLICATES_DIR = PDF_STORAGE_DIR / "duplicates"
DEBUG_FILE_PATH = PROJECT_ROOT / "debug_pricelists_content.html"

# Ensure directories exist
PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
DUPLICATES_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://www.rockwool.com"
TARGET_URL = "https://www.rockwool.com/hu/muszaki-informaciok/arlistak-es-prospektusok/"

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

class RockwoolBrochureScraper:
    """
    Enhanced scraper for Rockwool brochures and pricelists with proven 
    success methodology.
    """
    def __init__(self):
        self.documents = []
        self.visited_urls = set()
        self.downloaded_files = set()  # Track downloaded filenames
        self.duplicate_count = 0



    def _generate_unique_filename(self, base_filename: str, pdf_url: str) -> str:
        """
        Generates a unique filename for duplicates using URL hash.
        """
        name_part = Path(base_filename).stem
        extension = Path(base_filename).suffix
        
        # Create hash from URL for uniqueness
        url_hash = hashlib.md5(pdf_url.encode()).hexdigest()[:8]
        unique_filename = f"{name_part}_{url_hash}{extension}"
        
        return unique_filename

    async def _download_pdf(self, session: httpx.AsyncClient, pdf_url: str, doc_name: str) -> dict:
        """Downloads a single PDF with smart duplicate handling."""
        try:
            if not pdf_url.startswith('http'):
                pdf_url = urljoin(BASE_URL, pdf_url)
            
            logger.info(f"⬇️  Downloading: {pdf_url}")
            response = await session.get(pdf_url, follow_redirects=True)
            response.raise_for_status()

            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower():
                raise ValueError(f"Not a PDF file. Content-Type: {content_type}")

            safe_name = clean_filename(doc_name)
            base_filename = f"{safe_name}.pdf"
            
            # Smart duplicate handling
            if base_filename in self.downloaded_files:
                # Create unique filename for duplicate
                unique_filename = self._generate_unique_filename(base_filename, pdf_url)
                filepath = DUPLICATES_DIR / unique_filename
                self.duplicate_count += 1
                logger.info(
                    f"🔄 Duplicate detected, saving to duplicates: "
                    f"{unique_filename}"
                )
            else:
                # First occurrence - save to main directory
                filepath = PDF_STORAGE_DIR / base_filename
                self.downloaded_files.add(base_filename)

            with open(filepath, 'wb') as f:
                f.write(response.content)

            return {
                'status': 'success',
                'filename': filepath.name,
                'local_path': str(filepath),
                'file_size_bytes': len(response.content),
                'is_duplicate': base_filename in self.downloaded_files or 'duplicates' in str(filepath)
            }
        except Exception as e:
            logger.error(f"❌ Download failed for '{doc_name}': {e}")
            return {'status': 'failed', 'error': str(e)}

    async def fetch_live_content(self) -> str:
        """
        Fetches LIVE content from Rockwool brochures page.
        NO FALLBACK - always uses fresh, live data.
        """
        logger.info("🌐 Fetching LIVE brochure content from Rockwool website...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(TARGET_URL)
                response.raise_for_status()
                logger.info("✅ Successfully fetched LIVE brochure content!")
                
                # Save current content for debugging purposes only
                # (but never use it as fallback)
                try:
                    with open(DEBUG_FILE_PATH, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    logger.info(f"📄 Debug copy saved to: {DEBUG_FILE_PATH}")
                    
                    # Create timestamped backup for reference
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_file = f"debug_pricelists_{timestamp}.html"
                    with open(backup_file, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    logger.info(f"📄 Timestamped backup: {backup_file}")
                    
                except Exception as save_error:
                    logger.warning(f"⚠️  Could not save debug copy: {save_error}")
                
                return response.text
                
        except Exception as e:
            logger.error(f"❌ LIVE fetch failed: {e}")
            logger.error("🚫 NO FALLBACK AVAILABLE - Cannot proceed without live data")
            raise Exception(f"Failed to fetch live data from {TARGET_URL}: {e}")

    async def run(self):
        """Executes the entire scraping and downloading process with LIVE data."""
        logger.info("--- Starting Rockwool Brochure & Pricelist Scraper (LIVE MODE) ---")

        # Fetch LIVE HTML content
        html_content = await self.fetch_live_content()
        
        # Parse and store documents from the HTML
        self._parse_documents_from_html(html_content)

        # Download all found PDFs
        await self._download_all_pdfs()

        logger.info("--- Brochure & Pricelist Scraper Finished ---")
        self._log_summary()

    def _parse_documents_from_html(self, html_content: str):
        """Parses the brochure list from the raw HTML content."""
        props_pattern = r'data-component-name="O74DocumentationList"[^>]*data-component-props="({.*?})"'
        props_match = re.search(props_pattern, html_content, re.DOTALL)
        if not props_match:
            logger.error("❌ Could not find O74DocumentationList component data in HTML.")
            return

        props_str = props_match.group(1).replace('&quot;', '"')
        
        open_braces = 0
        end_index = -1
        for i, char in enumerate(props_str):
            if char == '{': open_braces += 1
            elif char == '}': open_braces -= 1
            if open_braces == 0:
                end_index = i + 1
                break
        
        if end_index == -1:
            logger.error("❌ Could not parse JSON from data-component-props.")
            return

        try:
            json_data = json.loads(props_str[:end_index])
            download_list = json_data.get('downloadList', [])

            for item in download_list:
                full_pdf_url = urljoin(BASE_URL, item.get("fileUrl"))
                if not any(d['pdf_url'] == full_pdf_url for d in self.documents):
                    self.documents.append({
                        "name": item.get("title", "Unnamed Document"),
                        "pdf_url": full_pdf_url
                    })
            
            logger.info(f"📊 Total documents found: {len(self.documents)}")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON data: {e}")

    async def _download_all_pdfs(self):
        """Downloads all PDFs with enhanced error handling and reporting."""
        if not self.documents: 
            logger.warning("⚠️  No documents to download")
            return

        logger.info(f"📥 Starting download of {len(self.documents)} documents...")
        successful_downloads = 0
        failed_downloads = 0
        
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as http_session:
            tasks = [self._download_pdf(http_session, doc['pdf_url'], doc['name']) for doc in self.documents]
            results = await asyncio.gather(*tasks)
            
            for result in results:
                if result.get('status') == 'success': 
                    successful_downloads += 1
                else: 
                    failed_downloads += 1
        
        self.successful_downloads = successful_downloads
        self.failed_downloads = failed_downloads

    def _log_summary(self):
        """Logs the enhanced final summary with duplicate information."""
        total_downloads = getattr(self, 'successful_downloads', 0)
        failed_downloads = getattr(self, 'failed_downloads', 0)
        unique_files = len(self.downloaded_files)
        
        logger.info("=" * 60)
        logger.info("📊 FINAL SUMMARY")
        logger.info("=" * 60)
        logger.info(f"📄 Documents found: {len(self.documents)}")
        logger.info(f"✅ Successful downloads: {total_downloads}")
        logger.info(f"❌ Failed downloads: {failed_downloads}")
        logger.info(f"📁 Unique files: {unique_files}")
        logger.info(f"🔄 Duplicates: {self.duplicate_count}")
        logger.info(f"📂 Main directory: {PDF_STORAGE_DIR.resolve()}")
        if self.duplicate_count > 0:
            logger.info(f"📂 Duplicates directory: {DUPLICATES_DIR.resolve()}")
        logger.info("=" * 60)

async def run():
    """Runner function for the enhanced brochure scraper."""
    scraper = RockwoolBrochureScraper()
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(run()) 