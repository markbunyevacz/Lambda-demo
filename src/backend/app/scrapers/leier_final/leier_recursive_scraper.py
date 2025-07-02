#!/usr/bin/env python3
"""
LEIER Recursive API-Powered Scraper
===================================

This is the definitive LEIER scraper. It combines API calls and simulated
browser actions to recursively discover and download all documents.

**Strategy:**
1.  **Initial API Call**: Fetches the main folder structure from the documents API.
2.  **Recursive Traversal**: For each folder found, it simulates a "click"
    by making a new API request for that folder's contents.
3.  **Direct Download**: Constructs the final download URL for each file and
    downloads it.
"""

import asyncio
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Set, Optional, Tuple, List, Any

import aiofiles
import httpx

# --- Configuration ---
BASE_URL = "https://www.leier.hu"
INITIAL_API_URL = "https://www.leier.hu/hu/documents/api/documents"

class LeierRecursiveScraper:
    """Recursively scrapes LEIER's documents API."""

    def __init__(self, test_mode: bool = False, max_concurrent: int = 10):
        self.test_mode = test_mode
        self.session_semaphore = asyncio.Semaphore(max_concurrent)
        
        # Paths
        current_dir = Path(__file__).resolve()
        project_root = current_dir.parents[3]
        self.base_dir = project_root / "src" / "downloads" / "leier_datasheets"
        self.reports_dir = project_root / "leier_scraping_reports"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Storage
        self.directories = {
            'documents': self.base_dir,
            'duplicates': self.base_dir / 'duplicates',
            'api_responses': self.base_dir / 'api_responses'
        }
        for directory in self.directories.values():
            directory.mkdir(parents=True, exist_ok=True)

        # Tracking
        self.discovered_docs: Set[Tuple[str, str, str]] = set() # url, title, category_path
        self.downloaded_files: Set[str] = set()
        self.failed_downloads: List[Tuple[str, str]] = []
        self.duplicate_files: Set[str] = set()
        self.visited_folders: Set[int] = set()

        self.setup_logging()

    def setup_logging(self):
        log_file = self.reports_dir / f'leier_recursive_scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("🚀 LEIER Recursive Scraper Initialized")

    async def fetch_folder_contents(self, folder_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Fetches the contents of a specific folder from the API."""
        if folder_id and folder_id in self.visited_folders:
            self.logger.info(f"Already visited folder {folder_id}, skipping.")
            return None
            
        url = INITIAL_API_URL if folder_id is None else f"{INITIAL_API_URL}/{folder_id}"
        self.logger.info(f"Querying API for folder: {url}")
        
        if folder_id:
            self.visited_folders.add(folder_id)

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.get(url)
                if response.status_code == 404 and folder_id is not None:
                     # This is expected for leaf-node documents, not an error
                    return None
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            self.logger.error(f"HTTP error for {url}: {e}")
        except json.JSONDecodeError:
            self.logger.error(f"Failed to decode JSON from {url}")
        return None

    async def traverse_and_discover(self, folder_id: Optional[int] = None, current_path: str = ""):
        """Recursively traverses the document hierarchy."""
        api_data = await self.fetch_folder_contents(folder_id)

        if not api_data:
            return

        # Save API response for debugging
        folder_name = "root" if folder_id is None else str(folder_id)
        sample_path = self.directories['api_responses'] / f'response_{folder_name}.json'
        async with aiofiles.open(sample_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(api_data, indent=2, ensure_ascii=False))

        # The actual documents/folders could be in 'documents' or 'children' key
        items = []
        if 'documents' in api_data and isinstance(api_data['documents'], list):
            items = api_data['documents']
        elif 'children' in api_data and isinstance(api_data['children'], list):
            items = api_data['children']
        
        for item in items:
            item_id = item.get('id')
            item_name = item.get('name', f"item_{item_id}")
            new_path = f"{current_path}/{item_name}" if current_path else item_name

            if item.get('is_folder') == 0:
                doc_url = f"{BASE_URL}/hu/dokumentumtar/{item_id}"
                self.discovered_docs.add((doc_url, item_name, new_path))
            elif item.get('is_folder') == 1:
                await self.traverse_and_discover(item_id, new_path)

    async def download_document(self, url: str, title: str, category_path: str):
        """Downloads a single document into its category folder."""
        # Sanitize category path to create valid directories
        sanitized_path = re.sub(r'[^\w\/\-]', '_', category_path)
        # remove the filename part from the category path
        sanitized_folder_path = Path(sanitized_path).parent
        
        target_dir = self.directories['documents'] / sanitized_folder_path
        target_dir.mkdir(parents=True, exist_ok=True)

        safe_filename = Path(sanitized_path).name
        if not Path(safe_filename).suffix:
            safe_filename += ".pdf"
            
        file_path = target_dir / safe_filename

        if file_path.exists():
            self.logger.warning(f"Duplicate, skipping: {file_path}")
            self.duplicate_files.add(url)
            return

        try:
            async with self.session_semaphore:
                async with httpx.AsyncClient(timeout=180.0, headers={'Referer': BASE_URL}) as client:
                    response = await client.get(url)
                    response.raise_for_status()

                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(response.content)
                
                self.logger.info(f"✅ Downloaded: {file_path}")
                self.downloaded_files.add(url)
        except Exception as e:
            self.logger.error(f"❌ Failed to download {url}: {e}")
            self.failed_downloads.append((url, str(e)))

    async def run(self):
        """Main execution logic."""
        start_time = datetime.now()
        self.logger.info("--- Starting LEIER Recursive Scraping Run ---")

        await self.traverse_and_discover()
        
        self.logger.info(f"Discovery complete. Found {len(self.discovered_docs)} total documents.")

        if self.test_mode:
            self.logger.info("Test mode enabled. Skipping downloads.")
        elif self.discovered_docs:
            self.logger.info(f"--- Downloading {len(self.discovered_docs)} documents ---")
            tasks = [self.download_document(url, title, path) for url, title, path in self.discovered_docs]
            await asyncio.gather(*tasks)
        else:
            self.logger.warning("No documents discovered to download.")

        self.generate_report(start_time)

    def generate_report(self, start_time: datetime):
        """Generates and saves a JSON report."""
        report = {
            "run_timestamp": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "test_mode": self.test_mode,
            "summary": {
                "documents_discovered": len(self.discovered_docs),
                "downloads_successful": len(self.downloaded_files),
                "downloads_failed": len(self.failed_downloads),
                "duplicates_found": len(self.duplicate_files),
            },
            "discovered_docs_sample": list(f"{path}" for _, _, path in self.discovered_docs)[:20],
            "failed_downloads": self.failed_downloads,
        }
        report_path = self.reports_dir / f'leier_recursive_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
        self.logger.info(f"📊 Report saved to {report_path}")

async def main():
    parser = argparse.ArgumentParser(description="LEIER Recursive API Scraper")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (discover only).",
    )
    args = parser.parse_args()
    scraper = LeierRecursiveScraper(test_mode=args.test)
    await scraper.run()

if __name__ == "__main__":
    import argparse
    asyncio.run(main()) 