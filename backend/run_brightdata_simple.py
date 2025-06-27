"""
Simple BrightData MCP Scraper for Rockwool
Direct MCP client usage without LangChain complexity
"""
import asyncio
import logging
import os
import json
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def scrape_with_brightdata_mcp():
    """Direct BrightData MCP scraping without LangChain"""
    
    # Check environment variables
    api_token = os.getenv('BRIGHTDATA_API_TOKEN')
    
    if not api_token:
        logger.error("BRIGHTDATA_API_TOKEN not found in environment")
        return {'success': False, 'error': 'Missing BRIGHTDATA_API_TOKEN'}
    
    try:
        # Import only basic MCP client
        from mcp import ClientSession, StdioServerParameters
        import subprocess
        
        logger.info("✅ MCP client loaded successfully")
        
    except ImportError as e:
        logger.error(f"❌ MCP dependencies missing: {e}")
        logger.error("Install with: pip install mcp")
        return {'success': False, 'error': f'Missing MCP dependencies: {e}'}
    
    logger.info("🚀 Starting BrightData MCP scraping for Rockwool...")
    
    target_url = "https://www.rockwool.com/hu/muszaki-informaciok/termekadatlapok/"
    
    try:
        # Start MCP server process - fix Windows PowerShell compatibility
        import platform
        npx_cmd = "npx.cmd" if platform.system() == "Windows" else "npx"
        
        server_process = subprocess.Popen([
            npx_cmd, "-y", "@brightdata/mcp"
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={**os.environ, "API_TOKEN": api_token}, shell=True)
        
        # Create MCP client session
        async with ClientSession(server_process.stdout, server_process.stdin) as session:
            await session.initialize()
            
            # List available tools
            tools_response = await session.list_tools()
            tools = tools_response.tools
            logger.info(f"📡 Available BrightData tools: {[tool.name for tool in tools]}")
            
            # Find the scraping tool
            scrape_tool = None
            for tool in tools:
                if 'scrape' in tool.name.lower() or 'html' in tool.name.lower():
                    scrape_tool = tool
                    break
            
            if not scrape_tool:
                logger.error("No scraping tool found in BrightData MCP")
                return {'success': False, 'error': 'No scraping tool available'}
            
            logger.info(f"Using tool: {scrape_tool.name}")
            
            # Call the scraping tool
            tool_response = await session.call_tool(
                scrape_tool.name,
                {"url": target_url}
            )
            
            # Extract content
            content = tool_response.content[0].text if tool_response.content else ""
            
            # Simple extraction - look for product patterns in HTML
            products = []
            if content:
                # Basic regex to find product data
                import re
                
                # Look for product titles and PDF URLs
                title_pattern = r'Monrock Max E termékadatlap|MŰSZAKI ADATLAP|Rockfall termékadatlap'
                pdf_pattern = r'https://[^"\']*\.pdf[^"\']*'
                
                titles = re.findall(title_pattern, content, re.IGNORECASE)
                pdf_urls = re.findall(pdf_pattern, content, re.IGNORECASE)
                
                for i, title in enumerate(titles):
                    product = {
                        'name': title,
                        'category': 'Termékadatlapok',
                        'pdf_url': pdf_urls[i] if i < len(pdf_urls) else None,
                        'scraped_at': datetime.now().isoformat()
                    }
                    products.append(product)
            
            result = {
                'success': True,
                'products_scraped': len(products),
                'products': products,
                'scraper_type': 'brightdata_mcp_simple',
                'target_url': target_url,
                'scraped_at': datetime.now().isoformat(),
                'raw_content_length': len(content)
            }
            
            logger.info(f"🎉 SUCCESS: {len(products)} products extracted")
            return result
    
    except Exception as e:
        logger.error(f"❌ BrightData MCP scraping failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'products_scraped': 0
        }
    finally:
        if 'server_process' in locals():
            server_process.terminate()


async def main():
    """Main function"""
    result = await scrape_with_brightdata_mcp()
    
    # Save results
    output_file = "rockwool_simple_mcp_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Results saved to: {output_file}")
    
    # Print summary
    if result['success']:
        print(f"\n✅ SUCCESS: {result['products_scraped']} products scraped")
        print(f"Raw content length: {result.get('raw_content_length', 0)} chars")
    else:
        print(f"\n❌ FAILED: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main()) 