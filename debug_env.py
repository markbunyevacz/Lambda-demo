#!/usr/bin/env python3
"""Debug script to test environment variable loading"""

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

print("=== ENVIRONMENT VARIABLES DEBUG ===")

# Check the variables that the agent needs
required_vars = [
    'BRIGHTDATA_API_TOKEN',
    'BRIGHTDATA_WEB_UNLOCKER_ZONE', 
    'ANTHROPIC_API_KEY'
]

missing_vars = []
for var in required_vars:
    value = os.getenv(var)
    print(f"{var}: {repr(value)}")
    
    # Same validation logic as in the agent
    if not value or value == f'your-{var.lower().replace("_", "-")}-here':
        missing_vars.append(var)
        print(f"  ❌ VALIDATION FAILED for {var}")
    else:
        print(f"  ✅ VALIDATION PASSED for {var}")

print(f"\nMissing variables: {missing_vars}")
print(f"All variables valid: {len(missing_vars) == 0}") 