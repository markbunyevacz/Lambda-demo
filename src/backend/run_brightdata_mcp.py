"""
BrightData MCP AI-Powered Scraper for Rockwool
==============================================

This script demonstrates the complete BrightData MCP (Model Context Protocol) integration
for intelligent web scraping. It combines:

1. BrightData's 48 specialized scraping tools (CAPTCHA solving, anti-detection)
2. Claude AI for intelligent content analysis and extraction
3. LangChain framework for agent orchestration
4. Async MCP server communication

Architecture:
- Python backend ←→ Node.js MCP Server ←→ BrightData Cloud Infrastructure
- Claude AI makes intelligent decisions about scraping strategies
- Results exported as structured JSON for further processing

Dependencies Required:
- mcp>=1.0.0 (MCP client/server communication)
- langchain-anthropic>=0.3.16 (Claude AI integration)
- langchain-mcp-adapters>=0.1.7 (MCP ↔ LangChain bridge)
- langgraph>=0.5.0 (Agent orchestration)
- Node.js runtime (BrightData MCP server)

Environment Variables Required:
- BRIGHTDATA_API_TOKEN (from https://brdta.com/techwithtim_mcp)
- ANTHROPIC_API_KEY (from console.anthropic.com)
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


async def scrape_rockwool_with_brightdata_mcp():
    """
    AI-Powered Rockwool Product Scraping with BrightData MCP
    
    This function orchestrates the complete scraping workflow:
    1. Environment validation (API keys, dependencies)
    2. MCP server initialization and tool loading
    3. Claude AI agent creation with specialized scraping instructions
    4. Intelligent content extraction and JSON parsing
    5. Result formatting and error handling
    
    Returns:
        dict: Scraping results with success status, product data, and metadata
    """
    
    # Step 1: Environment Validation
    # Check for required API credentials in environment variables
    api_token = os.getenv('BRIGHTDATA_API_TOKEN')        # BrightData proxy authentication
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')       # Claude AI model access
    
    # Fail fast if essential credentials are missing
    if not api_token:
        logger.error("BRIGHTDATA_API_TOKEN not found in environment")
        logger.error("Get your token from: https://brdta.com/techwithtim_mcp")
        return {'success': False, 'error': 'Missing BRIGHTDATA_API_TOKEN'}
        
    if not anthropic_key:
        logger.error("ANTHROPIC_API_KEY not found in environment")
        logger.error("Get your API key from: console.anthropic.com")
        return {'success': False, 'error': 'Missing ANTHROPIC_API_KEY'}
    
    try:
        # Step 2: Import MCP Dependencies
        # These imports will fail if dependencies aren't installed correctly
        from mcp import stdio_client, StdioServerParameters, ClientSession    # MCP client framework
        from langchain_anthropic import ChatAnthropic                        # Claude AI integration
        from langchain_mcp_adapters.tools import load_mcp_tools             # MCP ↔ LangChain bridge
        from langgraph.prebuilt import chat_agent_executor                  # Agent orchestration
        
        logger.info("✅ MCP dependencies loaded successfully")
        
    except ImportError as e:
        logger.error(f"❌ MCP dependencies missing: {e}")
        logger.error("Install with: pip install langchain langchain-anthropic langchain-mcp-adapters langgraph mcp httpx-sse")
        return {'success': False, 'error': f'Missing MCP dependencies: {e}'}
    
    logger.info("🚀 Starting BrightData MCP scraping for Rockwool...")
    
    # Step 3: Initialize Claude AI Model
    # Using Claude 3.5 Sonnet for advanced reasoning and content analysis
    model = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",    # Latest Claude model for best performance
        api_key=anthropic_key
    )
    
    # Step 4: Configure MCP Server Parameters
    # Handle Windows/Unix differences in NPX command execution
    import platform
    npx_cmd = "npx.cmd" if platform.system() == "Windows" else "npx"
    
    # MCP server configuration for BrightData integration
    server_params = StdioServerParameters(
        command=npx_cmd,                       # NPX command to run MCP server
        env={
            "API_TOKEN": api_token,            # Pass BrightData credentials to MCP server
            "WEB_UNLOCKER_ZONE": os.getenv(
                "BRIGHTDATA_WEB_UNLOCKER_ZONE", "web_unlocker"
            )
        },
        args=["-y", "@brightdata/mcp"]         # Auto-install and run BrightData MCP server
    )
    
    target_url = "https://www.rockwool.com/hu/muszaki-informaciok/termekadatlapok/"
    
    try:
        # Step 5: Establish MCP Server Connection
        # Create async communication channel with BrightData MCP server
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Step 6: Load Available Scraping Tools
                # Convert MCP tools to LangChain-compatible format
                tools = await load_mcp_tools(session)
                logger.info(f"📡 BrightData MCP tools loaded: {len(tools)} available")
                # Note: Should show 48 tools including Amazon, LinkedIn, Facebook, etc.
                
                # Step 7: Create AI Agent with Tool Access
                # Claude agent can now use all 48 BrightData scraping tools
                agent = chat_agent_executor.create_tool_calling_executor(model, tools)
                
                # Step 8: Design AI Scraping Instructions
                # Provide specialized prompts for Rockwool product extraction
                messages = [
                    {
                        "role": "system",
                        "content": """
                        You are an expert web scraping specialist with access to advanced BrightData tools.
                        Your mission: Extract comprehensive Rockwool product information from Hungarian website.
                        
                        SCRAPING STRATEGY:
                        1. Use mcp_brightdata_scrape_as_html or mcp_brightdata_scrape_as_markdown tools
                        2. Look for product datasheets (termékadatlapok) and technical specifications
                        3. Extract both visible content and downloadable PDF links
                        
                        TARGET DATA EXTRACTION:
                        - Product names (Magyar és English)
                        - Product categories (szigetelőanyag típusok)
                        - Technical specifications (λ értékek, tűzállóság, méretek)
                        - PDF download URLs (termékadatlapok)
                        - Application areas (alkalmazási területek)
                        - Product descriptions
                        
                        OUTPUT FORMAT:
                        Return structured JSON with array of products:
                        [{"name": "...", "category": "...", "specs": {...}, "pdf_url": "..."}]
                        
                        QUALITY REQUIREMENTS:
                        - Handle Hungarian language content correctly
                        - Validate all URLs before including
                        - Extract technical specifications completely
                        - Identify product relationships and categories
                        """
                    },
                    {
                        "role": "user",
                        "content": f"Scrape comprehensive Rockwool product data from: {target_url}\n\nFocus on termékadatlapok (product datasheets) and technical specifications."
                    }
                ]
                
                # Step 9: Execute AI-Powered Scraping
                logger.info(f"🔍 AI agent analyzing: {target_url}")
                logger.info("🤖 Claude is selecting optimal BrightData tools and strategies...")
                
                # Agent will intelligently choose from 48 available tools
                response = await agent.ainvoke({"messages": messages})
                
                # Step 10: Extract AI Response
                ai_response = response['messages'][-1].content
                logger.info("✅ AI scraping completed")
                logger.info(f"📄 Response length: {len(ai_response)} characters")
                
                # Step 11: Parse AI Response and Extract Product Data
                # Use regex to find JSON data within AI response text
                import re
                products_data = []
                
                # Try to find JSON code block first (preferred format)
                json_match = re.search(r'```json\s*(\[.*?\])\s*```', ai_response, re.DOTALL)
                if json_match:
                    try:
                        products_data = json.loads(json_match.group(1))
                        logger.info("✅ Successfully parsed JSON from code block")
                    except json.JSONDecodeError as e:
                        logger.warning(f"JSON parsing error in code block: {e}")
                
                # Fallback: look for any JSON array in the response
                if not products_data:
                    json_match = re.search(r'\[.*?\]', ai_response, re.DOTALL)
                    if json_match:
                        try:
                            products_data = json.loads(json_match.group(0))
                            logger.info("✅ Successfully parsed JSON from fallback search")
                        except json.JSONDecodeError as e:
                            logger.warning(f"JSON parsing error in fallback: {e}")
                
                # If no valid JSON found, log the issue
                if not products_data:
                    logger.warning("Could not extract valid JSON from AI response")
                    logger.debug(f"AI response sample: {ai_response[:500]}...")
                
                # Step 12: Format Final Results
                result = {
                    'success': True,
                    'products_scraped': len(products_data),
                    'products': products_data,
                    'scraper_type': 'brightdata_mcp_ai',
                    'target_url': target_url,
                    'scraped_at': datetime.now().isoformat(),
                    'ai_model_used': 'claude-3-5-sonnet-20241022',
                    'tools_available': len(tools),
                    'ai_response_raw': ai_response,  # Include for debugging/analysis
                    'metadata': {
                        'processing_time_seconds': (datetime.now() - start_time).total_seconds() if 'start_time' in locals() else None,
                        'mcp_server_type': 'brightdata',
                        'response_length_chars': len(ai_response),
                        'json_extraction_method': 'code_block' if json_match and 'json' in json_match.group(0) else 'fallback'
                    }
                }
                
                logger.info(f"🎉 SUCCESS: {len(products_data)} products extracted via AI-powered scraping")
                return result
                
    except Exception as e:
        logger.error(f"❌ BrightData MCP scraping failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'products_scraped': 0
        }


async def main():
    """Main function"""
    result = await scrape_rockwool_with_brightdata_mcp()
    
    # Save results
    output_file = "rockwool_brightdata_mcp_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Results saved to: {output_file}")
    
    # Print summary
    if result['success']:
        print(f"\n✅ SUCCESS: {result['products_scraped']} products scraped")
    else:
        print(f"\n❌ FAILED: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main()) 