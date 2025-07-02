#!/usr/bin/env python3
"""
ROCKWOOL Termékadatlapok Page Analysis
=====================================
This script analyzes the structure of the ROCKWOOL product datasheets page
to understand how products are organized and how to extract datasheet information.
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urljoin, urlparse

def analyze_rockwool_termekadatlapok():
    """Analyze the ROCKWOOL termékadatlapok page structure."""
    
    url = 'https://www.rockwool.com/hu/muszaki-informaciok/termekadatlapok/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print("=== ROCKWOOL TERMÉKADATLAPOK PAGE ANALYSIS ===")
        print(f"Analyzing: {url}")
        print()
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"📄 Content Length: {len(response.text):,} characters")
        print(f"📋 Content Type: {response.headers.get('Content-Type', 'Unknown')}")
        print()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Search for dynamic content components
        print("=== 🔍 DYNAMIC CONTENT ANALYSIS ===")
        data_components = soup.find_all(attrs={'data-component-name': True})
        print(f"Components with data-component-name: {len(data_components)}")
        
        for comp in data_components:
            comp_name = comp.get('data-component-name')
            print(f"  📦 {comp_name}")
            
            # Check for component props that might contain product data
            if comp.get('data-component-props'):
                props_preview = comp.get('data-component-props')[:100]
                print(f"     Props preview: {props_preview}...")
        
        print()
        
        # 2. Search for JSON data in script tags
        print("=== 📜 SCRIPT TAG ANALYSIS ===")
        script_tags = soup.find_all('script')
        json_scripts = 0
        product_data_scripts = 0
        
        for i, script in enumerate(script_tags):
            if script.string:
                script_content = script.string.strip()
                if script_content:
                    # Look for JSON-like content
                    if '{' in script_content and '}' in script_content:
                        json_scripts += 1
                    
                    # Look for product-related data
                    if any(keyword in script_content.lower() for keyword in ['termek', 'product', 'datasheet', 'pdf']):
                        product_data_scripts += 1
                        print(f"  🎯 Script {i+1}: Contains product-related data")
                        
                        # Try to extract JSON
                        try:
                            # Look for JSON objects
                            json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', script_content)
                            for j, match in enumerate(json_matches[:3]):  # Limit to first 3
                                try:
                                    parsed = json.loads(match)
                                    print(f"     JSON {j+1}: {type(parsed)} with {len(parsed) if isinstance(parsed, (dict, list)) else 'N/A'} items")
                                except:
                                    pass
                        except Exception as e:
                            pass
        
        print(f"Total script tags: {len(script_tags)}")
        print(f"Scripts with JSON-like content: {json_scripts}")
        print(f"Scripts with product data: {product_data_scripts}")
        print()
        
        # 3. Look for direct PDF links
        print("=== 📄 PDF LINKS ANALYSIS ===")
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf', re.I))
        print(f"Direct PDF links found: {len(pdf_links)}")
        
        for link in pdf_links[:10]:  # Show first 10
            href = link.get('href')
            text = link.get_text(strip=True)
            print(f"  📎 {text[:50]}... -> {href}")
        
        print()
        
        # 4. Search for download-related elements
        print("=== 💾 DOWNLOAD ELEMENTS ===")
        download_buttons = soup.find_all(['button', 'a'], text=re.compile(r'letölt|download|pdf', re.I))
        download_classes = soup.find_all(class_=re.compile(r'download|letolt|pdf', re.I))
        
        print(f"Download buttons/links: {len(download_buttons)}")
        print(f"Elements with download-related classes: {len(download_classes)}")
        
        # 5. Analyze product categories and structure
        print("=== 📂 PRODUCT CATEGORIES ===")
        category_keywords = {
            'tetőszigetelés': ['tetőszigetelés', 'roof', 'tető'],
            'homlokzat': ['homlokzat', 'facade', 'külső'],
            'gépészet': ['gépészet', 'hvac', 'mechanical'],
            'tűzvédelem': ['tűzvédelem', 'fire', 'conlit'],
            'hangszigetelés': ['hangszigetelés', 'acoustic', 'sound'],
            'ipari': ['ipari', 'industrial', 'steel']
        }
        
        for category, keywords in category_keywords.items():
            total_mentions = 0
            for keyword in keywords:
                mentions = len(soup.find_all(text=re.compile(keyword, re.I)))
                total_mentions += mentions
            print(f"  📁 {category.title()}: {total_mentions} mentions")
        
        print()
        
        # 6. Look for navigation or product listing structure
        print("=== 🗂️ PAGE STRUCTURE ===")
        
        # Find main content area
        main_content = soup.find('main') or soup.find('div', class_=re.compile(r'main|content|page'))
        if main_content:
            print("✅ Main content area found")
            
            # Look for product containers
            product_containers = main_content.find_all(['div', 'section', 'article'], 
                                                     class_=re.compile(r'product|termek|item|card'))
            print(f"  📦 Potential product containers: {len(product_containers)}")
            
            # Look for list items that might be products
            list_items = main_content.find_all('li')
            print(f"  📋 List items: {len(list_items)}")
            
            # Look for navigation elements
            nav_elements = main_content.find_all(['nav', 'ul'], class_=re.compile(r'nav|menu|category'))
            print(f"  🧭 Navigation elements: {len(nav_elements)}")
        else:
            print("❌ Main content area not clearly identified")
        
        print()
        
        # 7. Check for AJAX/API endpoints
        print("=== 🔗 API ENDPOINTS ===")
        api_patterns = [
            r'/api/',
            r'/ajax/',
            r'\.json',
            r'termek.*data',
            r'product.*data'
        ]
        
        api_mentions = 0
        for pattern in api_patterns:
            matches = re.findall(pattern, response.text, re.I)
            if matches:
                api_mentions += len(matches)
                print(f"  🎯 Pattern '{pattern}': {len(matches)} matches")
        
        if api_mentions == 0:
            print("  ℹ️ No obvious API endpoints found in static content")
        
        print()
        
        # 8. Save analysis results
        print("=== 💾 SAVING ANALYSIS ===")
        
        # Save full HTML for manual inspection
        with open('termekadatlapok_full.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"✅ Full HTML saved to 'termekadatlapok_full.html' ({len(response.text):,} chars)")
        
        # Save components data if found
        components_data = []
        for comp in data_components:
            components_data.append({
                'name': comp.get('data-component-name'),
                'props': comp.get('data-component-props', '')[:500],  # First 500 chars
                'tag': comp.name,
                'classes': comp.get('class', [])
            })
        
        with open('termekadatlapok_components.json', 'w', encoding='utf-8') as f:
            json.dump(components_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Components data saved to 'termekadatlapok_components.json'")
        
        # Summary
        print()
        print("=== 📊 ANALYSIS SUMMARY ===")
        print(f"🔍 Dynamic components found: {len(data_components)}")
        print(f"📜 Scripts with product data: {product_data_scripts}")
        print(f"📄 Direct PDF links: {len(pdf_links)}")
        print(f"💾 Download elements: {len(download_buttons) + len(download_classes)}")
        print(f"📦 Potential product containers: {len(product_containers) if 'product_containers' in locals() else 0}")
        
        if len(data_components) > 0:
            print("\n🎯 RECOMMENDATION: Focus on dynamic components - likely contain product data")
        elif len(pdf_links) > 0:
            print("\n🎯 RECOMMENDATION: Static PDF links available for direct extraction")
        else:
            print("\n🎯 RECOMMENDATION: May require JavaScript rendering or API discovery")
        
    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_rockwool_termekadatlapok() 