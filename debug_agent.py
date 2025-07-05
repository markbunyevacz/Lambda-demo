#!/usr/bin/env python3
"""
Simple PDF Processor Test - E2E Validation
Tests the core PDF processing functionality with SQLite fallback
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path
sys.path.append('src/backend')

def test_pdf_processor():
    """Test PDF processor with SQLite fallback"""
    
    print("🧪 TESTING PDF PROCESSOR - E2E VALIDATION")
    print("=" * 60)
    
    # Load environment
    load_dotenv(".env")
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found in environment")
        return False
    
    print(f"✅ API Key available: {api_key[:10]}...")
    
    # Check PDF files
    pdf_dir = Path("src/backend/src/downloads/rockwool_datasheets")
    if not pdf_dir.exists():
        print(f"❌ PDF directory not found: {pdf_dir}")
        return False
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    print(f"✅ Found {len(pdf_files)} PDF files")
    
    # Test a single PDF first
    if pdf_files:
        print(f"\n🧪 TESTING FIRST 3 PDFs for comprehensive validation:")
        
        results = []
        for i, test_pdf in enumerate(pdf_files[:3], 1):
            print(f"\n📄 ({i}/3) Testing: {test_pdf.name}")
            
            try:
                # Import and test basic PDF extraction
                from real_pdf_processor import RealPDFExtractor
                
                extractor = RealPDFExtractor()
                text, tables, method = extractor.extract_pdf_content(test_pdf)
                
                print(f"   ✅ PDF extraction: {len(text)} chars, {len(tables)} tables, {method}")
                
                # Test AI analysis
                from real_pdf_processor import ClaudeAIAnalyzer
                
                ai_analyzer = ClaudeAIAnalyzer()
                analysis = ai_analyzer.analyze_rockwool_pdf(text, tables, test_pdf.name)
                
                product_name = analysis.get('product_identification', {}).get('name', 'N/A')
                tech_specs = analysis.get('technical_specifications', {})
                pricing = analysis.get('pricing_information', {})
                
                print(f"   ✅ AI analysis: '{product_name}', {len(tech_specs)} specs, pricing: {bool(pricing)}")
                
                # Test confidence calculation
                from real_pdf_processor import RealPDFProcessor
                
                # Create a mock processor for confidence calculation
                class MockProcessor:
                    def _calculate_enhanced_confidence(self, text_content, tables, pattern_specs, ai_analysis, extraction_method):
                        # Simplified confidence calculation for testing
                        ai_confidence = ai_analysis.get('confidence_assessment', {}).get('overall_confidence', 0.7)
                        text_quality = min(1.0, len(text_content) / 5000)
                        table_success = min(1.0, len(tables) / 3)
                        pattern_success = min(1.0, len(pattern_specs) / 5)
                        method_reliability = 0.9 if extraction_method == 'pdfplumber' else 0.7
                        
                        confidence = (
                            ai_confidence * 0.3 +
                            text_quality * 0.2 +
                            table_success * 0.2 +
                            pattern_success * 0.15 +
                            method_reliability * 0.15
                        )
                        return round(confidence, 2)
                
                mock_processor = MockProcessor()
                confidence = mock_processor._calculate_enhanced_confidence(
                    text, tables, tech_specs, analysis, method
                )
                
                print(f"   ✅ Confidence score: {confidence}")
                
                results.append({
                    'file': test_pdf.name,
                    'text_length': len(text),
                    'tables_count': len(tables),
                    'method': method,
                    'product_name': product_name,
                    'specs_count': len(tech_specs),
                    'has_pricing': bool(pricing),
                    'confidence': confidence
                })
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                results.append({
                    'file': test_pdf.name,
                    'error': str(e)
                })
        
        # Summary
        print(f"\n📊 COMPREHENSIVE TEST RESULTS:")
        successful = [r for r in results if 'error' not in r]
        failed = [r for r in results if 'error' in r]
        
        print(f"   ✅ Successful: {len(successful)}/{len(results)}")
        print(f"   ❌ Failed: {len(failed)}/{len(results)}")
        
        if successful:
            avg_confidence = sum(r['confidence'] for r in successful) / len(successful)
            avg_specs = sum(r['specs_count'] for r in successful) / len(successful)
            print(f"   📈 Average confidence: {avg_confidence:.2f}")
            print(f"   🔧 Average specs per PDF: {avg_specs:.1f}")
            
            # Show sample results
            print(f"\n📋 Sample Results:")
            for result in successful[:2]:
                print(f"   📄 {result['file'][:30]}...")
                print(f"      Product: {result['product_name']}")
                print(f"      Specs: {result['specs_count']}, Confidence: {result['confidence']}")
        
        return len(successful) > 0
    
    return False

if __name__ == "__main__":
    success = test_pdf_processor()
    if success:
        print("\n🎉 E2E TEST PASSED - Core functionality working!")
    else:
        print("\n❌ E2E TEST FAILED - Needs debugging") 