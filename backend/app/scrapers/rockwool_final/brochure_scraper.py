"""
Rockwool Brochure Scraper - Direct Implementation
This module scrapes and downloads PDF brochures and pricelists
from the Rockwool Hungary "Árlisták és Prospektusok" page.
"""
import asyncio
import logging
import json
import httpx
import os
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
PDF_STORAGE_DIR = Path("downloads/rockwool_brochures")
BASE_URL = "https://www.rockwool.com"
TARGET_URL = "https://www.rockwool.com/hu/muszaki-informaciok/arlistak-es-prospektusok/"

class RockwoolBrochureScraper:
    """
    A direct scraper for Rockwool brochures and pricelists.
    """
    def __init__(self):
        PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        self.documents = []
        self.visited_urls = set()

    async def _download_pdf(self, session: httpx.AsyncClient, pdf_url: str, doc_name: str) -> dict:
        """Downloads a single PDF and returns its metadata."""
        # This function is identical to the one in the main scraper
        # and can be refactored into a shared utility later.
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
            filename = f"{safe_name}.pdf"
            filepath = PDF_STORAGE_DIR / filename

            with open(filepath, 'wb') as f:
                f.write(response.content)

            return {
                'status': 'success',
                'filename': filename,
                'local_path': str(filepath),
                'file_size_bytes': len(response.content)
            }
        except Exception as e:
            logger.error(f"❌ Download failed for '{doc_name}': {e}")
            return {'status': 'failed', 'error': str(e)}

    async def run(self):
        """Executes the entire multi-step scraping and downloading process."""
        logger.info("--- Starting Rockwool Multi-Page Brochure Scraper ---")
        
        self.visited_urls.add(TARGET_URL)
        
        # This part is also identical and can be refactored
        api_token = os.getenv('BRIGHTDATA_API_TOKEN')
        if not api_token:
            logger.error("❌ Missing BRIGHTDATA_API_TOKEN in .env file.")
            return

        try:
            from mcp.client.stdio import stdio_client, StdioServerParameters
            from mcp.client.session import ClientSession
        except ImportError:
            logger.error("❌ Missing 'mcp' library.")
            return

        import platform
        npx_cmd = "npx.cmd" if platform.system() == "Windows" else "npx"
        server_params = StdioServerParameters(command=npx_cmd, args=["-y", "@brightdata/mcp"], env={"API_TOKEN": api_token})

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    logger.info("✅ MCP Session Initialized.")
                    
                    # Step 1: Scrape the main page first
                    html_content = await self._scrape_html(session, TARGET_URL)
                    if not html_content:
                        # Save for debugging even on failure
                        with open("debug_brochures_main_failed.html", "w", encoding="utf-8") as f:
                            f.write(html_content or "")
                        return
                    
                    # Always parse the main page content
                    self._parse_brochures_from_html(html_content)

                    # Step 2: Find and scrape sub-pages from navigation
                    nav_links = self._find_nav_links(html_content)
                    logger.info(f"Found {len(nav_links)} navigation links to scrape.")
                    
                    for link in nav_links:
                        if link not in self.visited_urls:
                            self.visited_urls.add(link)
                            subpage_html = await self._scrape_html(session, link)
                            if subpage_html:
                                self._parse_brochures_from_html(subpage_html)
        except Exception as e:
            logger.error(f"❌ Scraping error: {e}", exc_info=True)
            return

        await self._download_all_pdfs()
        self._log_summary()

    async def _scrape_html(self, session, url: str) -> str | None:
        """Scrapes the HTML content of a single URL."""
        try:
            tool_name = "scrape_as_html"
            logger.info(f"🛠️  Calling {tool_name} on {url}")
            tool_result = await session.call_tool(tool_name, {"url": url})
            html_content = tool_result.content[0].text
            logger.info(f"✅ Scraped HTML content successfully from {url}.")
            return html_content
        except Exception as e:
            logger.error(f"❌ Failed to scrape {url}: {e}")
            return None
    
    def _find_nav_links(self, html_content: str) -> list[str]:
        """Finds additional pages to scrape from the 'Műszaki információ' box."""
        links = []
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            # The left-side navigation menu is contained in a <nav> tag with the class 'list-group'.
            nav_menu = soup.find('nav', class_='list-group')
            if nav_menu:
                # We find all anchor tags within this navigation menu.
                for a_tag in nav_menu.find_all('a', href=True):
                    links.append(urljoin(BASE_URL, a_tag['href']))
        except Exception as e:
            logger.error(f"Could not parse nav links: {e}")
        return links

    def _parse_brochures_from_html(self, html_content: str):
        """Parses the brochure list from the raw HTML content."""
        # This logic is copied from the working scraper.py
        props_pattern = r'data-component-name="O74DocumentationList"[^>]*data-component-props="({.*?})"'
        props_match = re.search(props_pattern, html_content, re.DOTALL)
        if not props_match:
            logger.error("Could not find O74DocumentationList component data in HTML.")
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
            logger.error("Could not parse JSON from data-component-props.")
            return

        json_data = json.loads(props_str[:end_index])
        download_list = json_data.get('downloadList', [])

        for item in download_list:
            full_pdf_url = urljoin(BASE_URL, item.get("fileUrl"))
            if not any(d['pdf_url'] == full_pdf_url for d in self.documents):
                self.documents.append({
                    "name": item.get("title", "Unnamed Document"),
                    "pdf_url": full_pdf_url
                })
        
        logger.info(f"📊 Total unique documents found so far: {len(self.documents)}")

    async def _download_all_pdfs(self):
        """Downloads all PDFs from the parsed document list."""
        if not self.documents: return

        logger.info(f"📥 Starting download of {len(self.documents)} documents...")
        successful_downloads = 0
        failed_downloads = 0
        
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as http_session:
            tasks = [self._download_pdf(http_session, doc['pdf_url'], doc['name']) for doc in self.documents]
            results = await asyncio.gather(*tasks)
            
            for result in results:
                if result.get('status') == 'success': successful_downloads += 1
                else: failed_downloads += 1
        
        self.successful_downloads = successful_downloads
        self.failed_downloads = failed_downloads

    def _log_summary(self):
        """Logs the final summary."""
        logger.info(f"✅ Successful downloads: {getattr(self, 'successful_downloads', 0)}")
        logger.info(f"❌ Failed downloads: {getattr(self, 'failed_downloads', 0)}")
        logger.info(f"📄 PDFs stored in: {PDF_STORAGE_DIR.resolve()}")

async def run():
    """Runner function for the brochure scraper."""
    scraper = RockwoolBrochureScraper()
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(run()) 