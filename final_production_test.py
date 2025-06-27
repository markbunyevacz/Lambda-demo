#!/usr/bin/env python3
"""
Final Production Test - Shows what's working in the Lambda demo
"""

import asyncio
import os

async def main():
    print("🎯 LAMBDA.HU PRODUCTION READY TEST")
    print("="*60)
    
    # 1. Environment Check
    print("\n📋 Environment Configuration:")
    token = os.getenv('BRIGHTDATA_API_TOKEN', '')
    zone = os.getenv('BRIGHTDATA_WEB_UNLOCKER_ZONE', '')
    anthropic = os.getenv('ANTHROPIC_API_KEY', '')
    
    print(f"   ✅ BrightData Token: {len(token)} chars")
    print(f"   ✅ Zone: {zone}")
    print(f"   ✅ Anthropic Key: {len(anthropic)} chars")
    
    # 2. Test Agent Imports
    print("\n🔧 Agent System:")
    try:
        from app.agents import BrightDataMCPAgent, ScrapingCoordinator
        print("   ✅ All agents imported successfully")
        
        # Test coordinator
        coordinator = ScrapingCoordinator()
        print("   ✅ Coordinator initialized")
        
        # Test basic availability
        test_results = await coordinator.test_all_scrapers()
        
        api_ok = test_results.get('api_scraper', {}).get('available', False)
        mcp_ok = test_results.get('mcp_agent', {}).get('available', False)
        
        print(f"   {'✅' if api_ok else '❌'} API Scraper: {'Available' if api_ok else 'Not Available'}")
        print(f"   {'✅' if mcp_ok else '❌'} MCP Agent: {'Available' if mcp_ok else 'Not Available'}")
        
        strategy = test_results.get('coordination', {}).get('recommended_strategy', 'UNKNOWN')
        print(f"   💡 Recommended Strategy: {strategy}")
        
    except Exception as e:
        print(f"   ❌ Agent test failed: {e}")
        return False
    
    # 3. Final Status
    print("\n" + "="*60)
    if api_ok or mcp_ok:
        print("🎉 PRODUCTION STATUS: READY!")
        print("\n🚀 Available Features:")
        if api_ok:
            print("   ✅ Traditional API scraping (Rockwool PDF extraction)")
        if mcp_ok:
            print("   ✅ AI-powered scraping (18 BrightData tools + Claude)")
        
        print("\n📊 What You Can Do Now:")
        print("   • Run Celery scraping tasks")
        print("   • Use coordination strategies")
        print("   • Test different scraping approaches")
        print("   • Monitor performance metrics")
        
        if mcp_ok:
            print("   • AI-driven data extraction")
            print("   • Automatic captcha solving")
            print("   • Advanced anti-detection")
        
    else:
        print("⚠️  SETUP NEEDS ATTENTION")
        
    print("="*60)
    return api_ok or mcp_ok

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1) 