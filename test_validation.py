#!/usr/bin/env python3
"""Test validation logic"""

from dotenv import load_dotenv
import os

load_dotenv()

print("=== VALIDATION TEST ===")

required_vars = [
    'BRIGHTDATA_API_TOKEN',
    'BRIGHTDATA_WEB_UNLOCKER_ZONE', 
    'ANTHROPIC_API_KEY'
]

missing_vars = []
for var in required_vars:
    value = os.getenv(var)
    placeholder = f'your-{var.lower().replace("_", "-")}-here'
    
    print(f"\n{var}:")
    print(f"  Value: {repr(value)}")
    print(f"  Placeholder: {repr(placeholder)}")
    print(f"  Is None?: {value is None}")
    print(f"  Is Empty?: {not value}")
    print(f"  Equals placeholder?: {value == placeholder}")
    
    # Same validation logic as in the agent
    if not value or value == placeholder:
        missing_vars.append(var)
        print(f"  ❌ VALIDATION FAILED")
    else:
        print(f"  ✅ VALIDATION PASSED")

print(f"\nFinal result:")
print(f"Missing variables: {missing_vars}")
print(f"MCP should be available: {len(missing_vars) == 0}") 