#!/usr/bin/env python3
"""
Final Production Test - BrightData MCP + ROCKWOOL Integration
Using existing Lambda.hu architecture with BrightData MCP tools
"""

import asyncio
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_brightdata_rockwool_integration():
    """
    Test BrightData MCP integration with existing ROCKWOOL scraper
    """
    print("🎯 Testing BrightData MCP + ROCKWOOL Integration")
    print("="*50)
    
    try:
        # Add app to path
        sys.path.append(str(Path(__file__).parent / "app"))
        
        # Import your existing scraper with BrightData integration
        from app.scraper.rockwool_scraper import scrape_with_brightdata_mcp
        
        # Test the integration
        print("📥 Running BrightData MCP scraping...")
        products = await scrape_with_brightdata_mcp(limit=3)
        
        if products:
            print(f"✅ Success! Found {len(products)} products")
            
            # Show sample product
            sample = products[0]
            print(f"\n📦 Sample Product:")
            print(f"   Name: {sample['name']}")
            print(f"   Category: {sample['category']}")
            print(f"   URL: {sample['source_url']}")
            print(f"   Tech Specs: {sample['technical_specs']}")
            
            return True
        else:
            print("❌ No products returned")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

async def main():
    """
    Main test function using your existing architecture
    """
    print("\n🚀 LAMBDA.HU - BRIGHTDATA MCP PRODUCTION TEST")
    print("Using existing architecture with BrightData MCP enhancement")
    print("="*60)
    
    # Test BrightData integration
    success = await test_brightdata_rockwool_integration()
    
    if success:
        print("\n🎉 Production test PASSED!")
        print("💡 Your PROS scope for ROCKWOOL PDF downloading is ready")
        print("💡 Data will be stored in your existing Lambda.hu database")
    else:
        print("\n❌ Production test FAILED!")
        print("💡 Check the BrightData MCP setup")

if __name__ == "__main__":
    asyncio.run(main()) 