"""
Rockwool Final Scraper - Direct Implementation
This module contains the final, working implementation for scraping
and downloading PDF datasheets from the Rockwool Hungary website.

It uses a direct scraping method with BrightData tools, bypassing
any complex AI agent logic for the scraping step itself.
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
logger = logging.getLogger(__name__)
PDF_STORAGE_DIR = Path("downloads/rockwool_datasheets")
BASE_URL = "https://www.rockwool.com"
TARGET_URL = "https://www.rockwool.com/hu/muszaki-informaciok/termekadatlapok/"

class RockwoolDirectScraper:
    """
    A direct scraper for Rockwool PDF datasheets.

    This class encapsulates the entire process:
    1. Connects to the BrightData MCP server.
    2. Directly calls the `scrape_as_html` tool.
    3. Parses the HTML to find product data and PDF URLs.
    4. Downloads all found PDFs into a structured directory.
    """
    def __init__(self):
        # Ensure storage directory exists
        PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        self.products = []

    async def _download_pdf(self, session: httpx.AsyncClient, pdf_url: str, product_name: str) -> dict:
        """Downloads a single PDF and returns its metadata."""
        try:
            if not pdf_url.startswith('http'):
                pdf_url = urljoin(BASE_URL, pdf_url)
            
            logger.info(f"⬇️  Downloading: {pdf_url}")
            response = await session.get(pdf_url, follow_redirects=True)
            response.raise_for_status()

            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower():
                raise ValueError(f"Not a PDF file. Content-Type: {content_type}")

            safe_name = re.sub(r'[^\w\s-]', '', product_name)[:50].strip()
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
            logger.error(f"❌ Download failed for '{product_name}': {e}")
            return {'status': 'failed', 'error': str(e)}

    async def run(self):
        """Executes the entire scraping and downloading process."""
        logger.info("--- Starting Rockwool Direct Scraper ---")
        
        api_token = os.getenv('BRIGHTDATA_API_TOKEN')
        if not api_token:
            logger.error("❌ Missing BRIGHTDATA_API_TOKEN in .env file. Cannot proceed.")
            return

        try:
            from mcp.client.stdio import stdio_client, StdioServerParameters
            from mcp.client.session import ClientSession
        except ImportError as e:
            logger.error(f"❌ Missing core 'mcp' library. Please run 'pip install mcp'. Error: {e}")
            return

        import platform
        npx_cmd = "npx.cmd" if platform.system() == "Windows" else "npx"

        server_params = StdioServerParameters(
            command=npx_cmd,
            args=["-y", "@brightdata/mcp"],
            env={"API_TOKEN": api_token}
        )

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    logger.info("✅ MCP Session Initialized.")
                    
                    tools_response = await session.list_tools()
                    available_tools = [t.name for t in tools_response.tools]
                    
                    scrape_tool_name = next((t for t in available_tools if "scrape_as_html" in t), None)
                    if not scrape_tool_name:
                        raise Exception("Could not find a suitable HTML scraping tool.")

                    logger.info(f"🛠️  Directly calling {scrape_tool_name} on {TARGET_URL}")
                    
                    tool_result = await session.call_tool(scrape_tool_name, {"url": TARGET_URL})
                    html_content = tool_result.content[0].text
                    logger.info(f"✅ Scraped HTML content successfully.")

                    # Parse and store products
                    self._parse_products_from_html(html_content)
                    if not self.products:
                        logger.warning("⚠️ No products were parsed from the HTML.")
                        return

        except Exception as e:
            logger.error(f"❌ An error occurred during scraping: {e}", exc_info=True)
            return

        # Download all found PDFs
        await self._download_all_pdfs()

        logger.info("--- Direct Scraper Finished ---")
        self._log_summary()

    def _parse_products_from_html(self, html_content: str):
        """Parses the product list from the raw HTML content."""
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
            self.products.append({
                "name": item.get("title", "Unnamed Product"),
                "description": item.get("description"),
                "category": item.get("category", "Uncategorized"),
                "pdf_url": item.get("fileUrl")
            })
        
        logger.info(f"📊 Successfully parsed {len(self.products)} products.")

    async def _download_all_pdfs(self):
        """Downloads all PDFs from the parsed product list."""
        if not self.products:
            return

        logger.info(f"📥 Starting download of {len(self.products)} PDFs...")
        successful_downloads = 0
        failed_downloads = 0
        
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as http_session:
            tasks = []
            for product in self.products:
                pdf_url = product.get('pdf_url')
                product_name = product.get('name', 'Unnamed Product')
                
                if pdf_url:
                    tasks.append(self._download_pdf(http_session, pdf_url, product_name))
            
            results = await asyncio.gather(*tasks)
            
            for result in results:
                if result.get('status') == 'success':
                    successful_downloads += 1
                else:
                    failed_downloads += 1
        
        self.successful_downloads = successful_downloads
        self.failed_downloads = failed_downloads

    def _log_summary(self):
        """Logs the final summary of the scraping and downloading process."""
        logger.info(f"✅ Successful downloads: {getattr(self, 'successful_downloads', 0)}")
        logger.info(f"❌ Failed downloads: {getattr(self, 'failed_downloads', 0)}")
        logger.info(f"📄 PDFs stored in: {PDF_STORAGE_DIR.resolve()}") 