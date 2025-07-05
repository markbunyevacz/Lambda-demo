"""
Simple MCP Orchestrator Test
===========================

Basic test to demonstrate the orchestrator without complex formatting.
"""

import asyncio
import time
from pathlib import Path

from .orchestrator import MCPOrchestrator


async def basic_test():
    """Run a basic test of the MCP orchestrator"""
    
    print("MCP Orchestrator Basic Test")
    print("=" * 40)
    
    # Find a test PDF
    test_pdf = None
    search_paths = [
        "src/downloads/rockwool_datasheets",
        "src/downloads"
    ]
    
    for path_str in search_paths:
        path = Path(path_str)
        if path.exists():
            pdf_files = list(path.glob("**/*.pdf"))
            if pdf_files:
                test_pdf = str(pdf_files[0])
                break
    
    if not test_pdf:
        print("No test PDF found")
        return
    
    print(f"Testing with: {Path(test_pdf).name}")
    
    # Initialize orchestrator
    orchestrator = MCPOrchestrator()
    
    # Run extraction
    start_time = time.time()
    
    try:
        golden_record = await orchestrator.extract_pdf(
            pdf_path=test_pdf,
            use_tiered_approach=True,
            max_cost_tier=2,  # Basic tiers only
            timeout_seconds=60
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"Success! Processing time: {processing_time:.1f}s")
        print(f"Confidence: {golden_record.overall_confidence:.2f}")
        print(f"Strategies: {len(golden_record.strategies_used)}")
        print(f"Fields extracted: {len(golden_record.extracted_data)}")
        
        if golden_record.requires_human_review:
            print("Requires human review")
        
        # Show key fields
        key_fields = ['product_name', 'technical_specs', 'full_text']
        for field in key_fields:
            if field in golden_record.extracted_data:
                value = golden_record.extracted_data[field]
                if isinstance(value, str):
                    preview = value[:50] + "..." if len(value) > 50 else value
                    print(f"{field}: {preview}")
                else:
                    print(f"{field}: {type(value).__name__}")
        
        return True
        
    except Exception as e:
        print(f"Failed: {e}")
        return False


if __name__ == "__main__":
    """Run the test"""
    result = asyncio.run(basic_test())
    print("Test completed:", "SUCCESS" if result else "FAILED") 