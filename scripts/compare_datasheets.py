#!/usr/bin/env python3
"""
Compare Scraped vs Website Datasheets
=====================================
This script compares what our scrapers found versus the official website datasheets.
"""

import json
import os
from pathlib import Path

def compare_scraped_vs_website():
    """Compare scraped files with website datasheets."""
    
    print("=== COMPARISON: SCRAPED vs WEBSITE DATASHEETS ===")
    print()
    
    try:
        # Load the complete datasheets list from website analysis
        with open('rockwool_datasheets_complete.json', 'r', encoding='utf-8') as f:
            website_datasheets = json.load(f)
        
        print(f"📄 WEBSITE DATASHEETS: {len(website_datasheets)} total")
        
        # Check our actual scraped files
        scraped_dir = Path('src/downloads/rockwool_datasheets')
        if scraped_dir.exists():
            scraped_files = list(scraped_dir.glob('*.pdf'))
            print(f"💾 ACTUALLY SCRAPED: {len(scraped_files)} PDF files")
            print()
            
            # Extract filenames for comparison
            website_filenames = set()
            for datasheet in website_datasheets:
                url = datasheet.get('fileUrl', '')
                if url:
                    filename = url.split('/')[-1].split('?')[0]
                    website_filenames.add(filename.lower())
            
            scraped_filenames = set()
            for file_path in scraped_files:
                filename = file_path.name.lower()
                # Remove duplicate markers like _0ab37780
                if '_' in filename:
                    parts = filename.split('_')
                    last_part = parts[-1].replace('.pdf', '')
                    if len(last_part) == 8 and last_part.isalnum():
                        filename = '_'.join(parts[:-1]) + '.pdf'
                scraped_filenames.add(filename)
            
            print("=== COVERAGE ANALYSIS ===")
            matched = website_filenames.intersection(scraped_filenames)
            missing = website_filenames - scraped_filenames
            extra = scraped_filenames - website_filenames
            
            coverage_pct = (len(matched) / len(website_filenames) * 100) if website_filenames else 0
            missing_pct = (len(missing) / len(website_filenames) * 100) if website_filenames else 0
            
            print(f"✅ MATCHED: {len(matched)} files ({coverage_pct:.1f}%)")
            print(f"❌ MISSING: {len(missing)} files ({missing_pct:.1f}%)")
            print(f"➕ EXTRA: {len(extra)} files (not in official list)")
            
            if missing:
                print()
                print("🔍 MISSING DATASHEETS (available on website but not scraped):")
                missing_items = []
                for datasheet in website_datasheets:
                    url = datasheet.get('fileUrl', '')
                    if url:
                        filename = url.split('/')[-1].split('?')[0].lower()
                        if filename in missing:
                            missing_items.append({
                                'title': datasheet.get('title', 'Unknown'),
                                'category': datasheet.get('category', 'Unknown'),
                                'filename': filename,
                                'url': url
                            })
                
                # Group by category
                by_category = {}
                for item in missing_items:
                    cat = item['category']
                    if cat not in by_category:
                        by_category[cat] = []
                    by_category[cat].append(item)
                
                for cat, items in by_category.items():
                    clean_cat = cat.replace('termékadatlapok*', '')
                    print(f"  📁 {clean_cat}: {len(items)} missing")
                    for item in items[:3]:
                        print(f"    • {item['title']} ({item['filename']})")
                    if len(items) > 3:
                        print(f"    ... and {len(items)-3} more")
            
            print()
            print("=== CATEGORY BREAKDOWN (Website) ===")
            categories = {}
            for datasheet in website_datasheets:
                cat = datasheet.get('category', 'Unknown').replace('termékadatlapok*', '')
                if cat not in categories:
                    categories[cat] = 0
                categories[cat] += 1
            
            for cat, count in sorted(categories.items()):
                print(f"  📂 {cat}: {count} datasheets")
            
            # Save missing list for potential scraping
            if missing_items:
                with open('missing_datasheets.json', 'w', encoding='utf-8') as f:
                    json.dump(missing_items, f, indent=2, ensure_ascii=False)
                print(f"\n💾 Missing datasheets list saved to 'missing_datasheets.json'")
            
        else:
            print("❌ No scraped files directory found")
            print("   Path checked: src/downloads/rockwool_datasheets")
            
            # Still show website categories
            print()
            print("=== WEBSITE CATEGORIES (Available for scraping) ===")
            categories = {}
            for datasheet in website_datasheets:
                cat = datasheet.get('category', 'Unknown').replace('termékadatlapok*', '')
                if cat not in categories:
                    categories[cat] = 0
                categories[cat] += 1
            
            for cat, count in sorted(categories.items()):
                print(f"  📂 {cat}: {count} datasheets")
    
    except FileNotFoundError as e:
        print(f"❌ Required file not found: {e}")
        print("Run extract_component_data.py first to get website datasheets.")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    compare_scraped_vs_website() 