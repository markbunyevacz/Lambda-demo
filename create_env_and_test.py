import os
import subprocess
import sys
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_env_file():
    """Create .env file with BrightData token"""
    env_content = "BRIGHTDATA_API_TOKEN=brd_super_proxy_26e3e92cd444bc9807fba28e135d62cdc962391e31203fe48d9d3dd7d874a88e"
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file with BrightData API token")

def add_main_block_to_scraper():
    """Add missing main execution block to rockwool_scraper_final.py"""
    main_block = '''

async def main():
    """Main function to run the scraper."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    scraper = RockwoolDirectScraper()
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    # Read current content
    with open('rockwool_scraper_final.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add main block if not present
    if 'if __name__ == "__main__"' not in content:
        with open('rockwool_scraper_final.py', 'w', encoding='utf-8') as f:
            f.write(content + main_block)
        print("✅ Added main execution block to rockwool_scraper_final.py")
    else:
        print("✅ Main execution block already exists")

def test_scraper():
    """Test the rockwool scraper"""
    print("\n🧪 Testing rockwool_scraper_final.py...")
    print("=" * 50)
    
    try:
        # Run the scraper with timeout
        result = subprocess.run(
            [sys.executable, 'rockwool_scraper_final.py'], 
            capture_output=True, 
            text=True, 
            timeout=300,  # 5 minutes timeout
            cwd=os.getcwd()
        )
        
        print("STDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)
        print(f"\nReturn code: {result.returncode}")
        
        # Check downloads
        downloads_dir = Path("downloads/rockwool_datasheets")
        if downloads_dir.exists():
            files = list(downloads_dir.glob("*.pdf"))
            print(f"\n📁 Downloads directory: {len(files)} PDF files")
            for f in files[:5]:
                print(f"  - {f.name} ({f.stat().st_size} bytes)")
            if len(files) > 5:
                print(f"  ... and {len(files) - 5} more files")
            
            return len(files) > 0  # Success if any files downloaded
        else:
            print("\n📁 Downloads directory not created")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Test timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def check_environment():
    """Check if required tools are available"""
    print("🔍 Checking environment...")
    
    # Check Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js: {result.stdout.strip()}")
        else:
            print("❌ Node.js not found")
    except:
        print("❌ Node.js not found")
    
    # Check npx
    try:
        npx_cmd = "npx.cmd" if os.name == 'nt' else "npx"
        result = subprocess.run([npx_cmd, '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npx: {result.stdout.strip()}")
        else:
            print("❌ npx not found")
    except:
        print("❌ npx not found")
    
    # Check Python packages
    try:
        import mcp
        print(f"✅ MCP library: {mcp.__version__}")
    except ImportError:
        print("❌ MCP library not found")
    
    try:
        import httpx
        print(f"✅ httpx library: {httpx.__version__}")
    except ImportError:
        print("❌ httpx library not found")

if __name__ == "__main__":
    print("🚀 Rockwool Scraper Test Suite")
    print("=" * 40)
    
    # Step 1: Check environment
    check_environment()
    
    # Step 2: Create .env file
    create_env_file()
    
    # Step 3: Fix scraper file
    add_main_block_to_scraper()
    
    # Step 4: Test scraper
    success = test_scraper()
    
    # Step 5: Summary
    print("\n" + "=" * 50)
    if success:
        print("🎉 SCRAPER TEST SUCCESSFUL!")
        print("✅ Ready for cleanup of redundant files")
    else:
        print("❌ SCRAPER TEST FAILED")
        print("🔧 Check the error messages above for troubleshooting")
    
    print("=" * 50) 