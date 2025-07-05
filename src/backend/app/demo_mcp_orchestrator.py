"""
MCP Orchestrator Demo Script
===========================

Simple demonstration of the advanced PDF extraction system.
Run this script to see the MCP orchestrator in action.
"""

import asyncio
import sys
from pathlib import Path

from mcp_orchestrator import MCPOrchestrator

# Add the app directory to path for imports
sys.path.append(str(Path(__file__).parent))


async def main():
    """Main demo function"""
    
    print("🚀 MCP Orchestrator Demo")
    print("=" * 50)
    print("Advanced PDF-RAG MCP-Orchestrated Extraction System")
    print("Multiple strategies | AI validation | Golden records")
    print()
    
    # Initialize orchestrator
    print("🔧 Initializing MCP Orchestrator...")
    orchestrator = MCPOrchestrator()
    print("✅ Orchestrator ready")
    print()
    
    # Find test PDFs
    print("📁 Looking for test PDFs...")
    test_pdf = None
    
    search_locations = [
        "../../downloads/rockwool_datasheets",
        "../downloads/rockwool_datasheets", 
        "downloads/rockwool_datasheets",
        "src/downloads/rockwool_datasheets"
    ]
    
    for location in search_locations:
        pdf_dir = Path(location)
        if pdf_dir.exists():
            pdf_files = list(pdf_dir.glob("*.pdf"))
            if pdf_files:
                test_pdf = str(pdf_files[0])
                print(f"✅ Found test PDF: {Path(test_pdf).name}")
                break
    
    if not test_pdf:
        print("❌ No test PDFs found in:")
        for location in search_locations:
            print(f"   - {location}")
        print()
        print("💡 To test the system:")
        print("   1. Place some PDF files in downloads/rockwool_datasheets/")
        print("   2. Run this script again")
        return
    
    print()
    
    # Run the extraction
    print("🎯 Running MCP orchestrated extraction...")
    print(f"📄 Processing: {Path(test_pdf).name}")
    print()
    
    try:
        # Extract using tiered approach
        golden_record = await orchestrator.extract_pdf(
            pdf_path=test_pdf,
            use_tiered_approach=True,
            max_cost_tier=2,  # Use basic tiers to avoid expensive AI calls
            timeout_seconds=60
        )
        
        print("✅ Extraction completed!")
        print()
        
        # Show results
        print("📊 RESULTS SUMMARY")
        print("-" * 30)
        print(f"Overall confidence: {golden_record.overall_confidence:.2f}")
        print(f"Completeness score: {golden_record.completeness_score:.1%}")
        print(f"Consistency score: {golden_record.consistency_score:.1%}")
        print(f"Strategies used: {', '.join(golden_record.strategies_used)}")
        print(f"Processing time: {golden_record.total_processing_time:.1f}s")
        review_status = 'Yes' if golden_record.requires_human_review else 'No'
        print(f"Requires review: {review_status}")
        print()
        
        # Show extracted fields
        if golden_record.extracted_data:
            print("📋 EXTRACTED FIELDS")
            print("-" * 30)
            for field_name, value in golden_record.extracted_data.items():
                if field_name == 'full_text':
                    preview = f"{len(str(value))} characters"
                elif isinstance(value, str):
                    preview = value[:60] + "..." if len(value) > 60 else value
                elif isinstance(value, dict):
                    preview = f"Dict with {len(value)} keys"
                else:
                    preview = str(value)
                
                print(f"  • {field_name}: {preview}")
        print()
        
        # Show confidence levels
        if golden_record.field_confidences:
            print("🎯 FIELD CONFIDENCE LEVELS")
            print("-" * 30)
            for field_name, conf in golden_record.field_confidences.items():
                level = conf.get_confidence_level().value
                score = conf.confidence_score
                print(f"  • {field_name}: {score:.2f} ({level})")
        print()
        
        # Show AI notes
        if golden_record.ai_adjudication_notes:
            print("🤖 AI ADJUDICATION NOTES")
            print("-" * 30)
            print(f"  {golden_record.ai_adjudication_notes}")
            print()
        
        # Show flagged fields
        flagged = golden_record.get_flagged_fields()
        if flagged:
            print("🚩 FIELDS REQUIRING REVIEW")
            print("-" * 30)
            for field_name, conf in flagged.items():
                print(f"  • {field_name}: {conf.notes}")
            print()
        
        # Show orchestrator stats
        stats = orchestrator.get_orchestrator_stats()
        print("📈 ORCHESTRATOR STATISTICS")
        print("-" * 30)
        print(f"  Total tasks: {stats['total_tasks']}")
        print(f"  Success rate: {stats['success_rate']:.1%}")
        print(f"  Average time: {stats['average_processing_time']:.1f}s")
        print(f"  Tier usage: {stats['tier_usage']}")
        print()
        
        print("🎉 Demo completed successfully!")
        print()
        print("✨ The MCP Orchestrator extracted data using multiple")
        print("   strategies and created a high-confidence golden record.")
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        print()
        print("🔍 This might be due to:")
        print("   - Missing PDF processing libraries")
        print("   - File permissions")
        print("   - PDF format issues")
        print()
        print("💡 Try running: pip install -r requirements.txt")


if __name__ == "__main__":
    """Run the demo"""
    print("Starting MCP Orchestrator demo...")
    asyncio.run(main()) 