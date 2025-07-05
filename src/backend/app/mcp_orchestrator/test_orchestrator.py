"""
Test Runner for MCP Orchestrator
===============================

Simple test script to demonstrate and validate the orchestrator functionality.
"""

import asyncio
import time
from pathlib import Path

from .orchestrator import MCPOrchestrator


async def test_single_pdf(orchestrator: MCPOrchestrator, pdf_path: str):
    """Test extraction on a single PDF file"""
    
    print(f"\n🔍 Testing PDF: {pdf_path}")
    print("-" * 50)
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return None
    
    start_time = time.time()
    
    try:
        # Run tiered extraction
        golden_record = await orchestrator.extract_pdf(
            pdf_path=pdf_path,
            use_tiered_approach=True,
            max_cost_tier=3,  # Skip expensive AI tier for testing
            timeout_seconds=120
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"✅ Extraction completed in {processing_time:.1f}s")
        print(f"📊 Overall confidence: {golden_record.overall_confidence:.2f}")
        print(f"📝 Strategies used: {', '.join(golden_record.strategies_used)}")
        print(f"🎯 Completeness: {golden_record.completeness_score:.1%}")
        print(f"🔄 Consistency: {golden_record.consistency_score:.1%}")
        
        if golden_record.requires_human_review:
            print("⚠️  Requires human review")
        
        # Show extracted data summary
        if golden_record.extracted_data:
                    print(f"\n📋 Extracted fields ({len(golden_record.extracted_data)}):")
        for field_name, value in golden_record.extracted_data.items():
            if isinstance(value, str) and len(value) > 100:
                value_preview = value[:97] + "..."
            else:
                value_preview = str(value)
            print(f"  • {field_name}: {value_preview}")
        
        # Show field confidences
        if golden_record.field_confidences:
            print("\n🎯 Field confidences:")
            for field_name, field_conf in golden_record.field_confidences.items():
                confidence_level = field_conf.get_confidence_level().value
                conf_score = field_conf.confidence_score
                print(f"  • {field_name}: {conf_score:.2f} ({confidence_level})")
        
        # Show flagged fields
        flagged = golden_record.get_flagged_fields()
        if flagged:
            print("\n🚩 Flagged fields needing review:")
            for field_name, field_conf in flagged.items():
                print(f"  • {field_name}: {field_conf.notes}")
        
        print(f"\n📝 AI Notes: {golden_record.ai_adjudication_notes}")
        
        return golden_record
        
    except Exception as e:
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"❌ Extraction failed after {processing_time:.1f}s")
        print(f"💥 Error: {str(e)}")
        return None


async def test_orchestrator_demo():
    """Run a demonstration of the MCP orchestrator"""
    
    print("🚀 MCP Orchestrator Demo")
    print("=" * 50)
    
    # Initialize orchestrator
    orchestrator = MCPOrchestrator()
    
    # Look for test PDFs in the downloads directory
    downloads_dir = Path("src/downloads")
    test_pdfs = []
    
    # Check for Rockwool PDFs
    rockwool_dir = downloads_dir / "rockwool_datasheets"
    if rockwool_dir.exists():
        pdf_files = list(rockwool_dir.glob("*.pdf"))
        if pdf_files:
            test_pdfs.extend(pdf_files[:3])  # Test first 3 PDFs
    
    # Check for other PDFs
    if downloads_dir.exists():
        other_pdfs = list(downloads_dir.glob("**/*.pdf"))
        for pdf in other_pdfs[:2]:  # Add 2 more PDFs
            if pdf not in test_pdfs:
                test_pdfs.append(pdf)
    
    if not test_pdfs:
        print("❌ No PDF files found for testing")
        print("💡 Expected locations:")
        print("   - src/downloads/rockwool_datasheets/*.pdf")
        print("   - src/downloads/**/*.pdf")
        return
    
    print(f"📁 Found {len(test_pdfs)} PDF files for testing")
    
    # Test each PDF
    results = []
    for i, pdf_path in enumerate(test_pdfs):
        result = await test_single_pdf(orchestrator, str(pdf_path))
        results.append({
            'pdf_path': str(pdf_path),
            'success': result is not None,
            'confidence': result.overall_confidence if result else 0.0,
            'requires_review': result.requires_human_review if result else True
        })
        
        # Small delay between tests
        if i < len(test_pdfs) - 1:
            await asyncio.sleep(1)
    
    # Summary
    print("\n📊 SUMMARY")
    print("=" * 50)
    
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    avg_confidence = sum(r['confidence'] for r in results) / total if total > 0 else 0
    
    print(f"✅ Successful extractions: {successful}/{total} ({successful/total:.1%})")
    print(f"🎯 Average confidence: {avg_confidence:.2f}")
    print(f"⚠️  Requiring review: {sum(1 for r in results if r['requires_review'])}")
    
    # Orchestrator stats
    stats = orchestrator.get_orchestrator_stats()
    print(f"\n🔧 Orchestrator Statistics:")
    print(f"  • Total tasks: {stats['total_tasks']}")
    print(f"  • Success rate: {stats['success_rate']:.1%}")
    print(f"  • Average processing time: {stats['average_processing_time']:.1f}s")
    print(f"  • Tier usage: {stats['tier_usage']}")
    
    return results


async def test_strategy_comparison():
    """Test and compare individual extraction strategies"""
    
    print("\n🔬 Strategy Comparison Test")
    print("=" * 50)
    
    # Find a test PDF
    test_pdf = None
    possible_paths = [
        "src/downloads/rockwool_datasheets",
        "src/downloads"
    ]
    
    for path_str in possible_paths:
        path = Path(path_str)
        if path.exists():
            pdf_files = list(path.glob("**/*.pdf"))
            if pdf_files:
                test_pdf = str(pdf_files[0])
                break
    
    if not test_pdf:
        print("❌ No test PDF found")
        return
    
    print(f"📄 Testing with: {test_pdf}")
    
    # Test individual strategies
    from .strategies import PDFPlumberStrategy, PyMuPDFStrategy
    
    strategies = [
        ("PDFPlumber", PDFPlumberStrategy()),
        ("PyMuPDF", PyMuPDFStrategy()),
        # OCR strategy takes too long for demo
    ]
    
    results = {}
    
    for name, strategy in strategies:
        print(f"\n🔧 Testing {name} strategy...")
        
        try:
            start_time = time.time()
            result = await strategy.extract(test_pdf)
            end_time = time.time()
            
            results[name] = result
            
            if result.success:
                print(f"  ✅ Success in {end_time - start_time:.1f}s")
                print(f"  📊 Confidence: {result.confidence_score:.2f}")
                print(f"  📝 Text length: {result.text_length}")
                print(f"  📊 Tables found: {result.tables_found}")
                print(f"  📄 Pages processed: {result.pages_processed}")
            else:
                print(f"  ❌ Failed: {result.error_message}")
                
        except Exception as e:
            print(f"  💥 Exception: {str(e)}")
    
    # Compare results
    if len([r for r in results.values() if r.success]) >= 2:
        print(f"\n⚖️  Strategy Comparison:")
        for name, result in results.items():
            if result.success:
                print(f"  • {name}: {result.confidence_score:.2f} confidence, "
                      f"{result.execution_time_seconds:.1f}s")


if __name__ == "__main__":
    """Run the demo if script is executed directly"""
    
    print("Starting MCP Orchestrator Tests...")
    
    async def main():
        await test_orchestrator_demo()
        await test_strategy_comparison()
    
    asyncio.run(main()) 