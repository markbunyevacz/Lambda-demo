#!/usr/bin/env python3
"""
LEIER API-Based Documents Scraper - Enhanced Recursive Version
=============================================================

This scraper targets the LEIER documents API directly with recursive folder 
exploration. It makes multiple API calls to fetch content from each subfolder.

**Key Features:**
- **API-First**: Calls the documents API and subfolder APIs
- **Recursive**: Makes separate API calls for each folder to get all documents
- **Efficient**: Avoids heavy browser automation
- **Robust Parsing**: Parses predictable JSON structure instead of fragile HTML
"""

import asyncio
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Set, Optional, Tuple, List

import aiofiles
import httpx

# --- Configuration ---
BASE_URL = "https://www.leier.hu"
API_BASE_URL = "https://www.leier.hu/hu/documents/api/documents"


class LeierAPIScraper:
    """Scrapes LEIER's documents via their internal API with recursive folder 
    exploration."""

    def __init__(self, test_mode: bool = False, max_concurrent: int = 5):
        self.test_mode = test_mode
        self.session_semaphore = asyncio.Semaphore(max_concurrent)
        
        # Setup paths
        current_dir = Path(__file__).resolve()
        project_root = current_dir.parents[3]
        self.base_dir = project_root / "src" / "downloads" / "leier_materials_api"
        self.reports_dir = project_root / "leier_scraping_reports"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Storage directories
        self.directories = {
            'documents': self.base_dir / 'documents',
            'duplicates': self.base_dir / 'duplicates',
            'api_responses': self.base_dir / 'api_responses'
        }
        for directory in self.directories.values():
            directory.mkdir(parents=True, exist_ok=True)

        # Tracking
        # (url, title, folder_path)
        self.discovered_docs: Set[Tuple[str, str, str]] = set()
        # (folder_id, folder_name) 
        self.discovered_folders: Set[Tuple[int, str]] = set()
        self.downloaded_files: Set[str] = set()
        self.failed_downloads: List[Tuple[str, str]] = []
        self.duplicate_files: Set[str] = set()
        self.api_calls_made = 0

        self.setup_logging()

    def setup_logging(self):
        """Sets up logging for the scraper."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.reports_dir / f'leier_api_scraper_{timestamp}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("🚀 LEIER API Scraper (Enhanced Recursive) Initialized")

    async def fetch_api_data(self, folder_id: Optional[int] = None) -> Optional[Dict]:
        """Fetches document data from the LEIER API, optionally for a specific 
        folder."""
        if folder_id:
            url = f"{API_BASE_URL}/{folder_id}"
            self.logger.info(f"Querying folder API: {url}")
        else:
            url = API_BASE_URL
            self.logger.info(f"Querying root API: {url}")
        
        self.api_calls_made += 1
        
        try:
            timeout = httpx.Timeout(45.0)
            async with httpx.AsyncClient(
                timeout=timeout, follow_redirects=True
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                self.logger.info(f"Successfully fetched API data from {url}")
                return response.json()
        except httpx.RequestError as e:
            self.logger.error(f"HTTP error while querying {url}: {e}")
        except json.JSONDecodeError:
            self.logger.error(f"Failed to decode JSON from {url}")
        except Exception as e:
            self.logger.error(f"Unexpected error querying {url}: {e}")
        return None

    def _get_api_items(self, api_data: Dict) -> Optional[List[Dict]]:
        """Extracts the list of items from the API response."""
        documents_key = 'documents' if 'documents' in api_data else 'children'
        
        if documents_key not in api_data:
            self.logger.warning(
                f"API data does not contain '{documents_key}' key"
            )
            return None

        items = api_data[documents_key]
        if not isinstance(items, list):
            self.logger.warning(f"'{documents_key}' is not a list")
            return None
        
        return items

    def _get_item_path(self, item: Dict, current_folder_path: str) -> str:
        """Constructs the full path for a given item."""
        item_name = item.get('name', f"item_{item.get('id', 'unknown')}")
        if current_folder_path:
            return f"{current_folder_path}/{item_name}"
        return item_name

    def _process_file_item(self, item: Dict, item_path: str):
        """Processes a file item from the API response."""
        if item.get('is_folder') == 0 and item.get('id'):
            doc_url = f"{BASE_URL}/hu/dokumentumtar/{item['id']}"
            item_name = item.get('name', 'Unknown Document')
            self.discovered_docs.add((doc_url, item_name, item_path))
            self.logger.debug(f"Found document: {item_name} at {item_path}")

    def _process_folder_item(self, item: Dict, item_path: str):
        """Processes a folder item from the API response."""
        if item.get('is_folder') == 1 and item.get('id'):
            folder_id = item['id']
            item_name = item.get('name', 'Unknown Folder')
            self.discovered_folders.add((folder_id, item_path))
            self.logger.debug(
                f"Found folder: {item_name} (ID: {folder_id}) at {item_path}"
            )
            
            # Process any immediate children if they exist
            if 'children' in item and isinstance(item.get('children'), list):
                self.parse_api_response(
                    {'children': item['children']}, item_path
                )
    
    def parse_api_response(self, api_data: Dict, folder_path: str = ""):
        """Parses the JSON response from the API to find document links and 
        folders."""
        items = self._get_api_items(api_data)
        if items is None:
            return
            
        for item in items:
            item_path = self._get_item_path(item, folder_path)
            self._process_file_item(item, item_path)
            self._process_folder_item(item, item_path)

    async def _save_folder_response(self, folder_id: int, folder_data: Dict):
        """Saves the API response for a folder to a file."""
        filename = f'folder_{folder_id}_response.json'
        folder_response_path = self.directories['api_responses'] / filename
        async with aiofiles.open(
            folder_response_path, 'w', encoding='utf-8'
        ) as f:
            await f.write(json.dumps(folder_data, indent=2, ensure_ascii=False))

    async def explore_folders_recursively(self):
        """Recursively explores all discovered folders to find documents."""
        processed_folders = set()
        
        while self.discovered_folders:
            current_folders = self.discovered_folders.copy()
            self.discovered_folders.clear()
            
            for folder_id, folder_path in current_folders:
                if folder_id in processed_folders:
                    continue
                    
                processed_folders.add(folder_id)
                self.logger.info(
                    f"Exploring folder: {folder_path} (ID: {folder_id})"
                )
                
                folder_data = await self.fetch_api_data(folder_id)
                if folder_data:
                    await self._save_folder_response(folder_id, folder_data)
                    self.parse_api_response(folder_data, folder_path)
                
                # Rate limiting
                await asyncio.sleep(0.5)

    def _create_download_directory(self, folder_path: str) -> Path:
        """Creates the directory structure for a downloaded file."""
        folder_parts = folder_path.split('/')
        current_dir = self.directories['documents']
        
        # Create nested folder structure
        for part in folder_parts[:-1]:  # Exclude the filename
            if part:  # Skip empty parts
                safe_part = re.sub(r'[^\w\.\-\s]', '_', part)
                current_dir = current_dir / safe_part
                current_dir.mkdir(exist_ok=True)
        return current_dir

    def _sanitize_filename(self, title: str) -> str:
        """Sanitizes a title to create a valid filename."""
        safe_filename = re.sub(r'[^\w\.\-\s]', '_', title)
        if not Path(safe_filename).suffix:
            safe_filename += ".pdf"
        return safe_filename

    async def download_document(self, url: str, title: str, folder_path: str):
        """Downloads a single document with folder organization."""
        current_dir = self._create_download_directory(folder_path)
        safe_filename = self._sanitize_filename(title)
        file_path = current_dir / safe_filename

        if file_path.exists():
            self.logger.warning(f"Duplicate found, skipping: {safe_filename}")
            self.duplicate_files.add(url)
            return

        try:
            async with self.session_semaphore:
                headers = {'Referer': BASE_URL}
                timeout = httpx.Timeout(120.0)
                async with httpx.AsyncClient(
                    timeout=timeout, headers=headers
                ) as client:
                    response = await client.get(url)
                    response.raise_for_status()

                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(response.content)
                
                download_path = f"{folder_path}/{safe_filename}"
                self.logger.info(f"✅ Downloaded: {download_path}")
                self.downloaded_files.add(url)
        except Exception as e:
            self.logger.error(f"❌ Failed to download {url}: {e}")
            self.failed_downloads.append((url, str(e)))

    async def _save_root_response(self, root_data: Dict) -> Path:
        """Saves the root API response to a file."""
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f'leier_api_response_{timestamp}.json'
        root_response_path = self.directories['api_responses'] / filename
        async with aiofiles.open(root_response_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(root_data, indent=2, ensure_ascii=False))
        return root_response_path

    async def run(self):
        """Main execution logic for the scraper."""
        start_time = datetime.now()
        self.logger.info("--- Starting LEIER API Recursive Scraping Run ---")

        # Step 1: Get root API data
        root_data = await self.fetch_api_data()
        if not root_data:
            self.logger.error("Failed to retrieve root API data. Aborting run.")
            return

        # Save root response
        root_response_path = await self._save_root_response(root_data)
        self.logger.info(f"Saved root API response to {root_response_path}")
        
        # Step 2: Parse root data to find initial folders and documents
        self.parse_api_response(root_data)
        initial_docs = len(self.discovered_docs)
        initial_folders = len(self.discovered_folders)
        
        msg = f"Initial parsing found {initial_docs} docs and {initial_folders} folders"
        self.logger.info(msg)
        
        # Step 3: Recursively explore all folders
        if self.discovered_folders:
            folder_count = len(self.discovered_folders)
            self.logger.info(
                f"--- Exploring {folder_count} folders recursively ---"
            )
            await self.explore_folders_recursively()
        
        total_docs = len(self.discovered_docs)
        self.logger.info(
            f"After recursive exploration: {total_docs} total docs discovered"
        )
        
        # Step 4: Download documents
        if self.test_mode:
            self.logger.info("Test mode enabled. Skipping downloads.")
        elif self.discovered_docs:
            doc_count = len(self.discovered_docs)
            self.logger.info(f"--- Downloading {doc_count} documents ---")
            tasks = [self.download_document(url, title, folder_path) 
                    for url, title, folder_path in self.discovered_docs]
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            self.logger.warning("No documents discovered to download.")

        self.generate_report(start_time)

    def generate_report(self, start_time: datetime):
        """Generates and saves a JSON report of the scraping run."""
        folders_explored_count = (
            len(self.discovered_folders) if hasattr(self, 'discovered_folders') else 0
        )
        report = {
            "run_timestamp": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "test_mode": self.test_mode,
            "target_url": API_BASE_URL,
            "api_calls_made": self.api_calls_made,
            "summary": {
                "folders_explored": folders_explored_count,
                "documents_discovered": len(self.discovered_docs),
                "downloads_successful": len(self.downloaded_files),
                "downloads_failed": len(self.failed_downloads),
                "duplicates_found": len(self.duplicate_files),
            },
            "discovered_docs_sample": [
                {"url": url, "title": title, "folder_path": folder_path} 
                for url, title, folder_path in list(self.discovered_docs)[:20]
            ],
            "failed_downloads": self.failed_downloads,
        }
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'leier_api_recursive_report_{timestamp}.json'
        report_path = self.reports_dir / filename
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
        self.logger.info(f"📊 Report saved to {report_path}")


async def main():
    parser = argparse.ArgumentParser(
        description="LEIER API-Based Documents Scraper - Enhanced Recursive"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (discover links but do not download).",
    )
    args = parser.parse_args()

    scraper = LeierAPIScraper(test_mode=args.test)
    await scraper.run()


if __name__ == "__main__":
    import argparse
    asyncio.run(main()) 