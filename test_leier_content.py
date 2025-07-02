#!/usr/bin/env python3
"""
Test script to examine LEIER document repository content
"""

import httpx
from bs4 import BeautifulSoup

def main():
    print("🔍 Testing LEIER document repository...")
    
    url = 'https://www.leier.hu/hu/dokumentumtar'
    print(f"Testing: {url}")
    
    try:
        response = httpx.get(url, timeout=30, follow_redirects=True)
        print(f"Status: {response.status_code}")
        print(f"Final URL: {response.url}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for PDF links
            pdf_links = soup.find_all('a', href=lambda x: x and '.pdf' in x.lower())
            print(f"\n📄 PDF links found: {len(pdf_links)}")
            for i, link in enumerate(pdf_links[:10]):
                text = link.get_text(strip=True)
                href = link.get('href')
                print(f"  {i+1}. {text[:60]}... -> {href}")
            
            # Look for any document links
            doc_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.dwg', '.dxf']
            doc_links = soup.find_all('a', href=lambda x: x and any(ext in x.lower() for ext in doc_extensions))
            print(f"\n📁 Document links found: {len(doc_links)}")
            
            # Look for buttons or interactive elements
            buttons = soup.find_all(['button', 'input'], type=['submit', 'button'])
            print(f"\n🔘 Buttons found: {len(buttons)}")
            
            # Look for forms
            forms = soup.find_all('form')
            print(f"📝 Forms found: {len(forms)}")
            
            # Look for specific LEIER content patterns
            print(f"\n🏗️ Content analysis:")
            
            # Check for JavaScript or dynamic content indicators
            scripts = soup.find_all('script')
            print(f"  JavaScript blocks: {len(scripts)}")
            
            # Look for data attributes that might indicate dynamic content
            dynamic_elements = soup.find_all(attrs={'data-src': True})
            print(f"  Dynamic elements: {len(dynamic_elements)}")
            
            # Look for typical document repository patterns
            selectors_to_test = [
                'a[href*="pdf"]',
                'a[href*="download"]', 
                'a[href*="letolt"]',
                '.document-link',
                '.file-link',
                '.download-link',
                '[data-file]',
                '[data-document]'
            ]
            
            print(f"\n🎯 Testing CSS selectors:")
            for selector in selectors_to_test:
                try:
                    elements = soup.select(selector)
                    print(f"  {selector}: {len(elements)} elements")
                except Exception as e:
                    print(f"  {selector}: Error - {e}")
            
            # Save sample HTML for analysis
            with open('leier_sample.html', 'w', encoding='utf-8') as f:
                f.write(response.text[:10000])  # First 10KB
            print(f"\n💾 Sample HTML saved to leier_sample.html")
            
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 