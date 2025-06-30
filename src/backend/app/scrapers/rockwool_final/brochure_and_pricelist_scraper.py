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
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import os

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Determine the project root based on the script's location
# Docker: script in /app/app/scrapers/rockwool_final, go up 3 levels to /app
PROJECT_ROOT = Path(__file__).resolve().parents[3]
PDF_STORAGE_DIR = (
    PROJECT_ROOT / "src" / "downloads" 
)
DUPLICATES_DIR = PDF_STORAGE_DIR / "duplicates"
DEBUG_FILE_PATH = PROJECT_ROOT / "debug_pricelists_content.html"

BASE_URL = "https://www.rockwool.com"
TARGET_URL = "https://www.rockwool.com/hu/muszaki-informaciok/arlistak-es-prospektusok/"

class RockwoolBrochureScraper:
    """
    Enhanced scraper for Rockwool brochures and pricelists with proven 
    success methodology.
    """
    def __init__(self):
        PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        DUPLICATES_DIR.mkdir(parents=True, exist_ok=True)
        self.documents = []
        self.visited_urls = set()
        self.downloaded_files = set()  # Track downloaded filenames
        self.duplicate_count = 0

    def _refresh_debug_file(self, debug_file_path: Path) -> bool:
        """
        Attempts to refresh the debug file with fresh content.
        Falls back to existing file if refresh fails.
        Returns True if using fresh content, False if using existing.
        """
        if debug_file_path.exists():
            file_age_hours = (
                datetime.now().timestamp() - debug_file_path.stat().st_mtime
            ) / 3600
            logger.info(f"📅 Existing debug file age: {file_age_hours:.1f} hours")
        else:
            logger.info("📅 No existing debug file found")
            file_age_hours = float('inf')
        
        try:
            # Attempt to fetch fresh content
            logger.info(
                "🔄 Attempting to refresh debug file with fresh content..."
            )
            import requests
            
            response = requests.get(TARGET_URL, timeout=30)
            response.raise_for_status()
            
            # Save fresh content with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"debug_pricelists_{timestamp}.html"
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # Update main debug file
            with open(debug_file_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            logger.info("✅ Fresh debug file saved (age: 0.0 hours)")
            logger.info(f"📄 Backup saved as: {backup_file}")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to refresh debug file: {e}")
            if debug_file_path.exists():
                logger.info(
                    f"📄 Using existing debug file "
                    f"(age: {file_age_hours:.1f} hours)"
                )
                return False
            else:
                logger.error("❌ No debug file available for scraping")
                raise FileNotFoundError(
                    f"No debug file available: {debug_file_path}"
                )

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

            safe_name = re.sub(r'[^\w\s-]', '', doc_name)[:50].strip()
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

    async def run(self):
        """Executes the entire scraping and downloading process."""
        logger.info("--- Starting Rockwool Brochure & Pricelist Scraper ---")

        # Step 1: Try to get fresh HTML content first
        self._refresh_debug_file(DEBUG_FILE_PATH)
        
        # Step 2: Use the debug file (fresh or existing)
        if DEBUG_FILE_PATH.exists():
            file_age = datetime.now().timestamp() - DEBUG_FILE_PATH.stat().st_mtime
            logger.info(f"🔍 Using debug file: {DEBUG_FILE_PATH} (age: {file_age/3600:.1f} hours)")
            
            with open(DEBUG_FILE_PATH, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse and store documents from the HTML
            self._parse_documents_from_html(html_content)
        else:
            logger.error(f"❌ No debug file available and live scraping failed.")
            return

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