#!/usr/bin/env python3
"""Debug version of agent validation"""

from dotenv import load_dotenv
import os
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DebugAgent:
    def __init__(self):
        self.mcp_available = False
        self._validate_environment()
        
    def _validate_environment(self):
        """Debug version of environment validation"""
        print("=== DEBUG VALIDATION ===")
        
        required_vars = [
            'BRIGHTDATA_API_TOKEN',
            'BRIGHTDATA_WEB_UNLOCKER_ZONE', 
            'ANTHROPIC_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            value = os.getenv(var)
            print(f"{var} = {repr(value)}")
            
            if not value or value == f'your-{var.lower().replace("_", "-")}-here':
                missing_vars.append(var)
                print(f"  ❌ FAILED")
            else:
                print(f"  ✅ PASSED")
        
        print(f"Missing vars: {missing_vars}")
        
        if missing_vars:
            logger.warning(f"Hiányzó környezeti változók: {missing_vars}")
            logger.warning("A BrightData MCP agent nem lesz elérhető")
            self.mcp_available = False
        else:
            logger.info("All environment variables valid")
            self.mcp_available = True
            
        print(f"MCP Available: {self.mcp_available}")

if __name__ == "__main__":
    agent = DebugAgent() 