#!/usr/bin/env python3
"""Test script for BrightData agent"""

from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Load environment variables first
load_dotenv()

# Add backend to path
backend_path = Path(__file__).parent / "src" / "backend"
sys.path.insert(0, str(backend_path))

print("=== TESTING BRIGHTDATA AGENT ===")

# Test environment variables
required_vars = ['BRIGHTDATA_API_TOKEN', 'BRIGHTDATA_WEB_UNLOCKER_ZONE', 'ANTHROPIC_API_KEY']
for var in required_vars:
    value = os.getenv(var)
    print(f"{var}: {'✅ SET' if value else '❌ MISSING'}")

print("\n=== IMPORTING AGENT ===")
try:
    from app.agents.brightdata_agent import BrightDataMCPAgent
    print("✅ Agent imported successfully")
    
    print("\n=== CREATING AGENT INSTANCE ===")
    agent = BrightDataMCPAgent()
    print(f"✅ Agent created. MCP Available: {agent.mcp_available}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 