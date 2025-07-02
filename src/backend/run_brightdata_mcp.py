#!/usr/bin/env python3
"""
BrightData MCP AI-Powered Targeted Scraper
==========================================

This script has been re-engineered to be a generic, AI-powered scraping utility.
It accepts a URL and a scraping objective from the command line, and uses the
Claude AI agent to intelligently execute the best BrightData tools to achieve
that objective.

**Usage:**
python run_brightdata_mcp.py <url> <scraping_objective>

**Example:**
python run_brightdata_mcp.py "https://www.leier.hu/hu/termekeink" "Extract all product category links (<a> tags)"
"""

import asyncio
import logging
import os
import json
import sys
import argparse
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_ai_scraper(target_url: str, objective: str):
    """
    Uses an AI agent to perform a targeted scrape on a given URL.
    """
    
    # Load variables directly from .env file to ensure they are passed
    load_dotenv()
    api_token = os.getenv('BRIGHTDATA_API_TOKEN')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    browser_user = os.getenv('BROWSER_USER')
    browser_pass = os.getenv('BROWSER_PASS')
    
    if not all([api_token, anthropic_key, browser_user, browser_pass]):
        logger.error("One or more required environment variables are missing from .env file.")
        return {'success': False, 'error': 'Missing environment variables'}

    try:
        from mcp import stdio_client, StdioServerParameters, ClientSession
        from langchain_anthropic import ChatAnthropic
        from langchain_mcp_adapters.tools import load_mcp_tools
        from langgraph.prebuilt import chat_agent_executor
    except ImportError as e:
        logger.error(f"Missing dependencies: {e}. Run 'pip install langchain langchain-anthropic langchain-mcp-adapters langgraph mcp'")
        return {'success': False, 'error': f'Missing dependencies: {e}'}

    logger.info(f"🚀 Starting AI-powered scrape for: {target_url}")
    
    model = ChatAnthropic(model="claude-3-5-sonnet-20240620", api_key=anthropic_key)
    
    import platform
    npx_cmd = "npx.cmd" if platform.system() == "Windows" else "npx"
    server_params = StdioServerParameters(
        command=npx_cmd,
        args=["-y", "@brightdata/mcp"],
        env={
            "API_TOKEN": api_token,
            "BROWSER_USER": browser_user,
            "BROWSER_PASS": browser_pass
        }
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                agent = chat_agent_executor.create_tool_calling_executor(model, tools)
                
                # Generic, targeted system prompt
                messages = [
                    {
                        "role": "system",
                        "content": """
                        You are a web scraping expert. Your task is to use the available BrightData tools to achieve the user's objective on the given URL.
                        - Use `scrape_as_html` for pages that require JavaScript rendering.
                        - Analyze the user's objective carefully.
                        - Return ONLY the requested data. If the user asks for links, return a JSON array of strings. If they ask for tables, return JSON representing the tables.
                        """
                    },
                    {
                        "role": "user",
                        "content": f"URL: {target_url}\nObjective: {objective}"
                    }
                ]
                
                response = await agent.ainvoke({"messages": messages})
                ai_response = response['messages'][-1].content
                
                # The calling script will parse the stdout, so we just print the result.
                print(ai_response)
                return {'success': True, 'response': ai_response}

    except Exception as e:
        logger.error(f"❌ An error occurred during AI scraping: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}

async def main():
    parser = argparse.ArgumentParser(description="AI-Powered Targeted Scraper")
    parser.add_argument("url", help="The target URL to scrape.")
    parser.add_argument("objective", help="A clear, natural language description of the scraping objective.")
    args = parser.parse_args()
    
    await run_ai_scraper(args.url, args.objective)

if __name__ == "__main__":
    asyncio.run(main()) 