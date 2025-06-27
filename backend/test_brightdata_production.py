#!/usr/bin/env python3
"""
Quick BrightData Production Test
Tests the corrected configuration with real credentials
"""

import asyncio
import os
import sys

def check_environment():
    """Check environment variables"""
    print("🔧 Environment Variables Check:")
    
    token = os.getenv("BRIGHTDATA_API_TOKEN", "NOT SET")
    zone = os.getenv("BRIGHTDATA_WEB_UNLOCKER_ZONE", "NOT SET") 
    browser = os.getenv("BRIGHTDATA_BROWSER_AUTH", "NOT SET")
    anthropic = os.getenv("ANTHROPIC_API_KEY", "NOT SET")
    
    print(f"   BRIGHTDATA_API_TOKEN: {token[:20]}..." if token != "NOT SET" else "   BRIGHTDATA_API_TOKEN: NOT SET")
    print(f"   BRIGHTDATA_WEB_UNLOCKER_ZONE: {zone}")
    print(f"   BRIGHTDATA_BROWSER_AUTH: {browser[:50]}..." if browser != "NOT SET" else "   BRIGHTDATA_BROWSER_AUTH: NOT SET")
    print(f"   ANTHROPIC_API_KEY: {'SET' if anthropic != 'NOT SET' and 'your-' not in anthropic else 'NOT SET'}")
    
    # Check for correct zone naming
    if zone == "web_unlocker":
        print("   ✅ Correct zone naming (web_unlocker)")
    elif zone == "web-unlocker":
        print("   ❌ Wrong zone naming! Should be 'web_unlocker' not 'web-unlocker'")
    else:
        print(f"   ⚠️  Unexpected zone: {zone}")
    
    return token != "NOT SET" and zone == "web_unlocker"

async def test_brightdata_connection():
    """Test BrightData MCP connection"""
    print("\n🚀 Testing BrightData MCP Connection...")
    
    try:
        # Add the app directory to path
        sys.path.insert(0, '/app')
        from app.agents import BrightDataMCPAgent
        
        agent = BrightDataMCPAgent()
        
        # Test connection
        result = await agent.test_mcp_connection()
        
        if result['success']:
            print("✅ BrightData MCP connection SUCCESSFUL!")
            print(f"   Message: {result.get('message', '')}")
            return True
        else:
            print("❌ BrightData MCP connection FAILED!")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

async def main():
    """Main test function"""
    print("="*60)
    print("🎯 BRIGHTDATA PRODUCTION SETUP TEST")
    print("="*60)
    
    # Test environment
    env_ok = check_environment()
    
    if not env_ok:
        print("\n❌ Environment configuration issues detected!")
        print("   Please check your .env file")
        return
    
    # Test BrightData connection
    connection_ok = await test_brightdata_connection()
    
    # Final status
    print("\n" + "="*60)
    if env_ok and connection_ok:
        print("🎉 PRODUCTION SETUP READY!")
        print("   All systems operational for production testing")
    else:
        print("⚠️  SETUP NEEDS ATTENTION")
        if not env_ok:
            print("   - Fix environment variables")
        if not connection_ok:
            print("   - Check BrightData credentials and connectivity")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main()) 