#!/usr/bin/env python3
"""
Extract ROCKWOOL O74DocumentationList Component Data
===================================================
This script extracts the product datasheets from the dynamic component data.
"""

import re
import json
import html

def extract_o74_documentation_data():
    """Extract and parse O74DocumentationList component data."""
    
    try:
        print("=== EXTRACTING O74DOCUMENTATIONLIST DATA ===")
        
        # Read the HTML file
        with open('termekadatlapok_full.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print(f"✅ HTML file loaded ({len(html_content):,} characters)")
        
        # Find the O74DocumentationList component
        pattern = r'data-component-name="O74DocumentationList"[^>]*data-component-props="([^"]*)"'
        match = re.search(pattern, html_content)
        
        if not match:
            print("❌ O74DocumentationList component not found")
            return
        
        props_str = match.group(1)
        print(f"✅ Component props found ({len(props_str):,} characters)")
        
        # Decode HTML entities
        props_str = html.unescape(props_str)
        
        # Parse JSON
        try:
            data = json.loads(props_str)
            print("✅ JSON parsed successfully")
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            print("Raw props preview:", props_str[:200])
            return
        
        print()
        print("=== COMPONENT ANALYSIS ===")
        print(f"Component Name: {data.get('componentName')}")
        print(f"Heading: {data.get('downloadItemsHeading')}")
        print(f"Item Type: {data.get('itemType')}")
        print(f"GUID: {data.get('guid')}")
        
        # Analyze categories structure
        if 'categories' in data:
            categories = data['categories']
            print()
            print("=== CATEGORIES STRUCTURE ===")
            print(f"Single Filter: {categories.get('singleFilter')}")
            
            if 'filters' in categories:
                filters = categories['filters']
                print(f"Main Filters: {len(filters)}")
                for f in filters:
                    print(f"  • {f.get('key')}: {f.get('value')} (count: {f.get('count')})")
            
            if 'filtersGroup' in categories:
                filter_groups = categories['filtersGroup']
                print(f"Filter Groups: {len(filter_groups)}")
                for i, group in enumerate(filter_groups[:3]):  # Show first 3
                    print(f"  Group {i+1}: {group.get('key')} ({group.get('count')} items)")
        
        # Check for download list
        if 'downloadList' in data:
            downloads = data['downloadList']
            print()
            print(f"📄 TOTAL DATASHEETS FOUND: {len(downloads)}")
            
            if len(downloads) > 0:
                # Analyze by category
                categories = {}
                for item in downloads:
                    cat = item.get('category', 'Unknown')
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append(item)
                
                print()
                print("📂 DATASHEETS BY CATEGORY:")
                for cat, items in sorted(categories.items()):
                    print(f"  📁 {cat}: {len(items)} items")
                
                # Show sample items
                print()
                print("📋 SAMPLE DATASHEETS:")
                for i, item in enumerate(downloads[:10]):
                    title = item.get('title', 'No title')
                    file_url = item.get('fileUrl', 'No URL')
                    category = item.get('category', 'No category')
                    file_size = item.get('fileSize', 'Unknown size')
                    language = item.get('language', 'Unknown language')
                    
                    print(f"  {i+1:2d}. {title}")
                    print(f"      📂 Category: {category}")
                    print(f"      📏 Size: {file_size}")
                    print(f"      🌐 Language: {language}")
                    print(f"      🔗 URL: {file_url}")
                    print()
                
                # Save the full download list
                with open('rockwool_datasheets_complete.json', 'w', encoding='utf-8') as f:
                    json.dump(downloads, f, indent=2, ensure_ascii=False)
                print(f"✅ Complete datasheets list saved to 'rockwool_datasheets_complete.json'")
                
                # Create summary report
                summary = {
                    'total_datasheets': len(downloads),
                    'categories': {cat: len(items) for cat, items in categories.items()},
                    'sample_items': downloads[:5]  # First 5 items
                }
                
                with open('rockwool_datasheets_summary.json', 'w', encoding='utf-8') as f:
                    json.dump(summary, f, indent=2, ensure_ascii=False)
                print(f"✅ Summary report saved to 'rockwool_datasheets_summary.json'")
                
                # Generate download URLs list
                urls = [item.get('fileUrl') for item in downloads if item.get('fileUrl')]
                with open('rockwool_datasheet_urls.txt', 'w', encoding='utf-8') as f:
                    for url in urls:
                        f.write(f"{url}\n")
                print(f"✅ Download URLs saved to 'rockwool_datasheet_urls.txt' ({len(urls)} URLs)")
                
        else:
            print("❌ No 'downloadList' found in component data")
            print("Available keys:", list(data.keys()))
            
            # Save the full component data for manual inspection
            with open('o74_component_full_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("✅ Full component data saved to 'o74_component_full_data.json'")
        
    except FileNotFoundError:
        print("❌ termekadatlapok_full.html not found. Run analyze_termekadatlapok.py first.")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    extract_o74_documentation_data() 