"""
Rockwool Datasheet Scraper
--------------------------

Purpose:
This script is responsible for scraping and downloading all official product
datasheets (PDFs) from the Rockwool Hungary website. It is the primary tool
for gathering detailed technical information about products.

Key Features:
- Uses a robust "debug file" strategy for reliability, refreshing from live
  data when possible.
- Handles duplicate files intelligently by saving them to a separate
  subdirectory with unique names.
- Fully asynchronous downloads for high performance.

This is a final, production-ready version.
"""
import asyncio
import logging
import json
import httpx
import os
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin

# --- Configuration ---
logger = logging.getLogger(__name__)
PDF_STORAGE_DIR = Path("downloads/final_test")
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

    async def _download_pdf(self, session: httpx.AsyncClient, pdf_url: str, product_name: str, existing_files: set) -> dict:
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
            base_filename = f"{safe_name}.pdf"
            
            # Handle duplicates by putting them in subdirectory
            if base_filename in existing_files:
                duplicates_dir = PDF_STORAGE_DIR / "duplicates"
                duplicates_dir.mkdir(exist_ok=True)
                
                # Create unique filename with URL hash
                import hashlib
                url_hash = hashlib.md5(pdf_url.encode()).hexdigest()[:8]
                filename = f"{safe_name}_{url_hash}.pdf"
                filepath = duplicates_dir / filename
                
                logger.info(f"📁 Duplicate detected, saving to duplicates/{filename}")
            else:
                filename = base_filename
                filepath = PDF_STORAGE_DIR / filename
                existing_files.add(base_filename)

            with open(filepath, 'wb') as f:
                f.write(response.content)

            return {
                'status': 'success',
                'filename': filename,
                'local_path': str(filepath),
                'file_size_bytes': len(response.content),
                'is_duplicate': base_filename in existing_files or 'duplicates' in str(filepath)
            }
        except Exception as e:
            logger.error(f"❌ Download failed for '{product_name}': {e}")
            return {'status': 'failed', 'error': str(e)}

    async def run(self):
        """Executes the entire scraping and downloading process."""
        logger.info("--- Starting Rockwool Direct Scraper ---")
        
        debug_file = "debug_termekadatlapok.html"
        
        # Step 1: Try to get fresh HTML content first
        await self._refresh_debug_file(debug_file)
        
        # Step 2: Use the debug file (fresh or existing)
        if Path(debug_file).exists():
            file_age = datetime.now().timestamp() - Path(debug_file).stat().st_mtime
            logger.info(f"🔍 Using debug file: {debug_file} (age: {file_age/3600:.1f} hours)")
            
            with open(debug_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse and store products from the HTML
            self._parse_products_from_html(html_content)
            
            if not self.products:
                logger.warning("⚠️ No products were parsed from debug file.")
                return
        else:
            logger.error("❌ No debug file available and live scraping failed.")
            return

        # Download all found PDFs
        await self._download_all_pdfs()

        logger.info("--- Direct Scraper Finished ---")
        self._log_summary()

    async def _refresh_debug_file(self, debug_file: str):
        """Attempts to refresh the debug file with fresh HTML content."""
        logger.info("🔄 Attempting to refresh debug file with fresh content...")
        
        api_token = os.getenv('BRIGHTDATA_API_TOKEN')
        if not api_token:
            logger.warning("⚠️ No BRIGHTDATA_API_TOKEN, using existing debug file")
            return

        try:
            from mcp.client.stdio import stdio_client, StdioServerParameters
            from mcp.client.session import ClientSession
        except ImportError:
            logger.warning("⚠️ MCP library not available, using existing debug file")
            return

        try:
            import platform
            npx_cmd = "npx.cmd" if platform.system() == "Windows" else "npx"

            server_params = StdioServerParameters(
                command=npx_cmd,
                args=["-y", "@brightdata/mcp"],
                env={"API_TOKEN": api_token}
            )

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    tools_response = await session.list_tools()
                    available_tools = [t.name for t in tools_response.tools]
                    
                    scrape_tool_name = next((t for t in available_tools if "scrape_as_html" in t), None)
                    if not scrape_tool_name:
                        logger.warning("⚠️ No HTML scraping tool found")
                        return

                    logger.info(f"🌐 Fetching fresh content from {TARGET_URL}")
                    tool_result = await session.call_tool(scrape_tool_name, {"url": TARGET_URL})
                    fresh_html = tool_result.content[0].text
                    
                    # Save fresh content with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    fresh_debug_file = f"debug_termekadatlapok_{timestamp}.html"
                    
                    with open(fresh_debug_file, 'w', encoding='utf-8') as f:
                        f.write(fresh_html)
                    
                    # Update the main debug file if fresh content contains the component
                    if 'data-component-name="O74DocumentationList"' in fresh_html:
                        with open(debug_file, 'w', encoding='utf-8') as f:
                            f.write(fresh_html)
                        logger.info(f"✅ Debug file refreshed successfully")
                    else:
                        logger.warning(f"⚠️ Fresh content missing O74DocumentationList, keeping old debug file")
                        logger.info(f"🔍 Fresh content saved as: {fresh_debug_file}")

        except Exception as e:
            logger.warning(f"⚠️ Failed to refresh debug file: {e}")
            logger.info("📋 Will use existing debug file if available")

    async def _attempt_live_scraping(self):
        """Attempts to scrape the website live using BrightData MCP."""
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

                    # Check if content is blocked by cookie dialog
                    if "CybotCookiebotDialog" in html_content:
                        logger.warning("⚠️  Cookie consent dialog detected. Attempting to bypass...")
                        html_content = self._extract_content_from_cookie_blocked_page(html_content)
                        
                        if not html_content:
                            logger.error("❌ Could not bypass cookie dialog.")
                            return

                    # Parse and store products
                    self._parse_products_from_html(html_content)

        except Exception as e:
            logger.error(f"❌ Live scraping failed: {e}", exc_info=True)

    def _extract_content_from_cookie_blocked_page(self, html_content: str) -> str:
        """
        Extracts the actual page content from behind the CookieBot dialog.
        The O74DocumentationList component exists in the HTML but is hidden by the overlay.
        """
        try:
            # Look for the O74DocumentationList component in the full HTML
            # Even though it's behind the cookie dialog, the data is still there
            if 'data-component-name="O74DocumentationList"' in html_content:
                logger.info("✅ Found O74DocumentationList component behind cookie dialog")
                return html_content  # Return the full HTML, we'll parse it anyway
            
            # If we can't find the component, try to look for alternative patterns
            if 'downloadList' in html_content:
                logger.info("✅ Found downloadList data in HTML")
                return html_content
                
            logger.error("❌ Could not find product data even behind cookie dialog")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error extracting content from cookie-blocked page: {e}")
            return None

    def _parse_products_from_html(self, html_content: str):
        """Parses the product list from the raw HTML content."""
        # Try multiple patterns for finding the component data
        patterns = [
            r'data-component-name="O74DocumentationList"[^>]*data-component-props="({.*?})"',
            r'data-component-name="[^"]*DocumentationList[^"]*"[^>]*data-component-props="({.*?})"',
            r'data-component-props="({[^}]*downloadList[^}]*})"'
        ]
        
        props_match = None
        for pattern in patterns:
            props_match = re.search(pattern, html_content, re.DOTALL)
            if props_match:
                logger.info(f"✅ Found component data using pattern: {pattern[:50]}...")
                break
        
        if not props_match:
            logger.error("Could not find O74DocumentationList component data in HTML.")
            # Debug: Save HTML content for inspection
            with open("debug_termekadatlapok_failed.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info("🔍 Debug: HTML content saved to debug_termekadatlapok_failed.html")
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
        duplicate_downloads = 0
        existing_files = set()
        
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as http_session:
            tasks = []
            for product in self.products:
                pdf_url = product.get('pdf_url')
                product_name = product.get('name', 'Unnamed Product')
                
                if pdf_url:
                    tasks.append(self._download_pdf(http_session, pdf_url, product_name, existing_files))
            
            results = await asyncio.gather(*tasks)
            
            for result in results:
                if result.get('status') == 'success':
                    successful_downloads += 1
                    if result.get('is_duplicate'):
                        duplicate_downloads += 1
                else:
                    failed_downloads += 1
        
        self.successful_downloads = successful_downloads
        self.failed_downloads = failed_downloads
        self.duplicate_downloads = duplicate_downloads

    def _log_summary(self):
        """Logs the final summary of the scraping and downloading process."""
        logger.info(f"✅ Successful downloads: {getattr(self, 'successful_downloads', 0)}")
        logger.info(f"❌ Failed downloads: {getattr(self, 'failed_downloads', 0)}")
        logger.info(f"📁 Duplicate files: {getattr(self, 'duplicate_downloads', 0)}")
        logger.info(f"📄 PDFs stored in: {PDF_STORAGE_DIR.resolve()}")
        if getattr(self, 'duplicate_downloads', 0) > 0:
            logger.info(f"📁 Duplicates stored in: {PDF_STORAGE_DIR.resolve()}/duplicates")

async def main():
    """Main function to run the scraper."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    scraper = RockwoolDirectScraper()
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main()) 