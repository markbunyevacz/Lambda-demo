#!/usr/bin/env python3

import pymupdf4llm
from pathlib import Path

def test_pymupdf4llm_extraction():
    """Test PyMuPDF4LLM extraction and compare with expected content"""
    
    input_pdf = Path('src/downloads/rockwool_datasheets/Airrock HD termékadatlap.pdf')
    
    print("=== TESTING PyMuPDF4LLM EXTRACTION ===")
    
    # Test 1: Extract page 1 (second page, 0-indexed)
    print("\n1. Extracting page 1 (second page)...")
    try:
        md_page1 = pymupdf4llm.to_markdown(str(input_pdf), pages=[1], table_strategy='lines')
        print(f"✅ Page 1 extracted successfully ({len(md_page1)} characters)")
    except Exception as e:
        print(f"❌ Error extracting page 1: {e}")
        return
    
    # Test 2: Check for specific content that should be on page 2
    expected_content = [
        "A ROCKWOOL kőzetgyapot tulajdonságai",
        "Általános tudnivalók", 
        "A bazaltkő természetes erejével",
        "Tűzvédelem",
        "Hőszigetelés", 
        "Hangszigetelés",
        "Tartósság",
        "Esztétika",
        "Páraáteresztés",
        "Újrahasznosítás",
        "Ellenáll akár 1000°C-os hőmérsékletnek",
        "Energiamegtakarítás és optimális belső hőmérséklet"
    ]
    
    print("\n2. Checking for expected content...")
    found_count = 0
    for content in expected_content:
        if content in md_page1:
            print(f"✅ \"{content}\" - FOUND")
            found_count += 1
        else:
            print(f"❌ \"{content}\" - MISSING")
    
    print(f"\n📊 SUMMARY: {found_count}/{len(expected_content)} expected content items found")
    
    # Test 3: Show full page content
    print("\n3. Full page 1 content:")
    print("=" * 80)
    print(md_page1)
    print("=" * 80)
    
    # Test 4: Compare with full document extraction
    print("\n4. Testing full document extraction...")
    try:
        md_full = pymupdf4llm.to_markdown(str(input_pdf), table_strategy='lines')
        print(f"✅ Full document extracted successfully ({len(md_full)} characters)")
        
        # Save results for comparison
        output_dir = Path('reports/pymupdf4llm_tests')
        output_dir.mkdir(exist_ok=True, parents=True)
        
        (output_dir / 'page1_only.md').write_bytes(md_page1.encode('utf-8'))
        (output_dir / 'full_document.md').write_bytes(md_full.encode('utf-8'))
        
        print(f"📁 Results saved to: {output_dir}")
        
    except Exception as e:
        print(f"❌ Error extracting full document: {e}")

if __name__ == "__main__":
    test_pymupdf4llm_extraction() 