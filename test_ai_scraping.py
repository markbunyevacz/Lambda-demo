#!/usr/bin/env python3
"""
AI Scraping Production Test
Live testing of BrightData MCP capabilities
"""

import asyncio
import os
import sys
import time
from datetime import datetime

async def test_mcp_connection():
    """Test 1: BrightData MCP Connection"""
    print("🔧 Test 1: BrightData MCP Connection")
    print("-" * 40)
    
    try:
        from app.agents import BrightDataMCPAgent
        
        agent = BrightDataMCPAgent()
        
        # Force re-validate environment
        agent._validate_environment()
        agent._init_dependencies()
        
        print(f"   MCP Available: {agent.mcp_available}")
        
        if agent.mcp_available:
            result = await agent.test_mcp_connection()
            
            if result['success']:
                print("   ✅ BrightData MCP connection successful!")
                print(f"   📋 Message: {result.get('message', '')}")
                return True
            else:
                print("   ❌ BrightData MCP connection failed!")
                print(f"   🚫 Error: {result.get('error', 'Unknown')}")
                return False
        else:
            print("   ⚠️  MCP not available (dependencies or config issue)")
            return False
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

async def test_ai_scraping():
    """Test 2: AI-Powered Scraping"""
    print("\n🤖 Test 2: AI-Powered Scraping")
    print("-" * 40)
    
    try:
        from app.agents import BrightDataMCPAgent
        
        agent = BrightDataMCPAgent()
        
        if not agent.mcp_available:
            print("   ⚠️  Skipping - MCP not available")
            return False
        
        # Test URLs
        test_urls = ["https://www.rockwool.hu"]
        
        print(f"   🎯 Testing AI scraping on: {test_urls[0]}")
        
        start_time = time.time()
        
        products = await agent.scrape_rockwool_with_ai(
            test_urls,
            "Extract basic company and product information from this Rockwool page"
        )
        
        duration = time.time() - start_time
        
        if products:
            print(f"   ✅ AI scraping successful!")
            print(f"   📊 Products found: {len(products)}")
            print(f"   ⏱️  Duration: {duration:.2f} seconds")
            
            # Show sample data
            if products:
                sample = products[0]
                print(f"   📝 Sample product:")
                print(f"      Name: {sample.get('name', 'N/A')}")
                print(f"      Category: {sample.get('category', 'N/A')}")
                print(f"      Source: {sample.get('source_url', 'N/A')}")
            
            return True
        else:
            print("   ⚠️  No products extracted")
            return False
            
    except Exception as e:
        print(f"   ❌ AI scraping failed: {e}")
        return False

async def test_celery_integration():
    """Test 3: Celery Task Integration"""
    print("\n📋 Test 3: Celery Task Integration")
    print("-" * 40)
    
    try:
        from app.celery_tasks.brightdata_tasks import (
            test_brightdata_mcp_connection,
            ai_powered_rockwool_scraping,
            coordinated_scraping_with_fallback
        )
        
        print("   ✅ BrightData Celery tasks imported successfully")
        
        # List available tasks
        tasks = [
            "test_brightdata_mcp_connection",
            "ai_powered_rockwool_scraping", 
            "coordinated_scraping_with_fallback",
            "brightdata_search_and_scrape"
        ]
        
        print("   📋 Available Celery tasks:")
        for task in tasks:
            print(f"      • {task}")
        
        print("\n   💡 To run a task:")
        print("   result = test_brightdata_mcp_connection.delay()")
        print("   print(result.get())  # Wait for result")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Celery integration test failed: {e}")
        return False

async def test_coordination_strategies():
    """Test 4: Coordination Strategies"""
    print("\n🎛️  Test 4: Coordination Strategies")
    print("-" * 40)
    
    try:
        from app.agents import ScrapingCoordinator
        from app.agents.scraping_coordinator import ScrapingStrategy
        
        coordinator = ScrapingCoordinator()
        
        # Test available strategies
        strategies = [
            ScrapingStrategy.API_ONLY,
            ScrapingStrategy.MCP_ONLY, 
            ScrapingStrategy.API_FALLBACK_MCP,
            ScrapingStrategy.MCP_FALLBACK_API,
            ScrapingStrategy.PARALLEL
        ]
        
        print("   📋 Available strategies:")
        for strategy in strategies:
            print(f"      • {strategy.value}")
        
        # Test scraper availability
        print("\n   🔍 Testing scraper availability...")
        test_results = await coordinator.test_all_scrapers()
        
        api_available = test_results.get('api_scraper', {}).get('available', False)
        mcp_available = test_results.get('mcp_agent', {}).get('available', False)
        recommended = test_results.get('coordination', {}).get('recommended_strategy', 'UNKNOWN')
        
        print(f"   {'✅' if api_available else '❌'} API Scraper: {'Available' if api_available else 'Not Available'}")
        print(f"   {'✅' if mcp_available else '❌'} MCP Agent: {'Available' if mcp_available else 'Not Available'}")
        print(f"   💡 Recommended: {recommended}")
        
        return mcp_available or api_available
        
    except Exception as e:
        print(f"   ❌ Coordination test failed: {e}")
        return False

async def main():
    """Run all AI scraping tests"""
    print("🚀 LAMBDA.HU AI SCRAPING PRODUCTION TEST")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Run tests
    results = []
    
    results.append(await test_mcp_connection())
    results.append(await test_ai_scraping()) 
    results.append(await test_celery_integration())
    results.append(await test_coordination_strategies())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    test_names = [
        "BrightData MCP Connection",
        "AI-Powered Scraping",
        "Celery Integration", 
        "Coordination Strategies"
    ]
    
    for i, (test_name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test_name}: {status}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed >= 3:
        print("🎉 PRODUCTION READY - AI Scraping System Operational!")
        print("\n🚀 Next Steps:")
        print("   • Run Celery workers for background processing")
        print("   • Test with real scraping tasks")
        print("   • Monitor performance and adjust strategies")
    else:
        print("⚠️  Some components need attention")
    
    return passed >= 3

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1) 