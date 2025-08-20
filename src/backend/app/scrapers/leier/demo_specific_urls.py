#!/usr/bin/env python3
"""
LEIER Specific URLs Demo
========================

Demonstrates downloading product documents from specific LEIER URLs:
- Product page: https://www.leier.hu/hu/termekek/leier-beton-pillerzsaluzo-elem-25
- Category pages: https://www.leier.hu/hu/termekeink/pillerzsaluzo-elem
- File server: https://www.leier.hu/uploads/files/
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from pathlib import Path

async def demo_product_page():
    """Demo: Extract documents from a specific product page."""
    print("🚀 Demo: Extracting documents from specific product page")
    
    url = "https://www.leier.hu/hu/termekek/leier-beton-pillerzsaluzo-elem-25"
    print(f"Target: {url}")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        html = response.text
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find PDF links
    pdf_links = []
    for link in soup.find_all('a'):
        href = link.get('href', '')
        if href and '.pdf' in href.lower():
            full_url = urljoin("https://www.leier.hu", href)
            title = link.get_text(strip=True)
            pdf_links.append((full_url, title))
    
    print(f"✅ Found {len(pdf_links)} PDF documents:")
    for i, (pdf_url, title) in enumerate(pdf_links[:5], 1):
        print(f"  {i}. {title}")
        print(f"     URL: {pdf_url}")
    
    return pdf_links

async def demo_category_page():
    """Demo: Extract product links from category page."""
    print("\n🚀 Demo: Finding products in category page")
    
    url = "https://www.leier.hu/hu/termekeink/pillerzsaluzo-elem"
    print(f"Target: {url}")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        html = response.text
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find product links
    product_links = []
    for link in soup.find_all('a'):
        href = link.get('href', '')
        if href and '/termekek/' in href:
            full_url = urljoin("https://www.leier.hu", href)
            name = link.get_text(strip=True)
            if name and full_url not in [p[0] for p in product_links]:
                product_links.append((full_url, name))
    
    print(f"✅ Found {len(product_links)} product links:")
    for i, (prod_url, name) in enumerate(product_links[:3], 1):
        print(f"  {i}. {name}")
        print(f"     URL: {prod_url}")
    
    return product_links

async def demo_file_server():
    """Demo: Check file server directory."""
    print("\n🚀 Demo: Checking file server directory")
    
    url = "https://www.leier.hu/uploads/files/"
    print(f"Target: {url}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 403:
                print("⚠️  Directory browsing disabled (403 Forbidden)")
                print("   Files must be accessed via direct links from product pages")
            elif response.status_code == 404:
                print("⚠️  Directory not found (404)")
            else:
                response.raise_for_status()
                html = response.text
                
                soup = BeautifulSoup(html, 'html.parser')
                file_links = []
                for link in soup.find_all('a'):
                    href = link.get('href', '')
                    if href and any(ext in href.lower() for ext in ['.pdf', '.doc', '.zip']):
                        full_url = urljoin(url, href)
                        file_links.append((full_url, href))
                
                print(f"✅ Found {len(file_links)} files:")
                for i, (file_url, filename) in enumerate(file_links[:5], 1):
                    print(f"  {i}. {filename}")
                
                return file_links
                
    except Exception as e:
        print(f"❌ Error accessing file server: {e}")
        return []

async def demo_download_sample(pdf_links):
    """Demo: Download a sample PDF."""
    if not pdf_links:
        print("\n⚠️  No PDFs found to download")
        return
    
    print("\n🚀 Demo: Downloading sample PDF")
    
    # Take first PDF
    pdf_url, title = pdf_links[0]
    
    # Sanitize filename
    safe_title = re.sub(r'[^\w\s\-]', '_', title)
    if not safe_title.endswith('.pdf'):
        safe_title += '.pdf'
    
    print(f"Downloading: {title}")
    print(f"From: {pdf_url}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(pdf_url)
            response.raise_for_status()
            
            # Save to current directory
            file_path = Path(safe_title)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            file_size = file_path.stat().st_size / 1024  # KB
            print(f"✅ Downloaded: {safe_title} ({file_size:.1f} KB)")
            
    except Exception as e:
        print(f"❌ Download failed: {e}")

async def main():
    """Run all demos."""
    print("=" * 60)
    print("LEIER Website Document Extraction Demo")
    print("=" * 60)
    
    # Demo 1: Product page documents
    pdf_links = await demo_product_page()
    
    # Demo 2: Category page products
    product_links = await demo_category_page()
    
    # Demo 3: File server
    file_links = await demo_file_server()
    
    # Demo 4: Download sample
    await demo_download_sample(pdf_links)
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"✅ PDF documents found: {len(pdf_links)}")
    print(f"✅ Product pages found: {len(product_links)}")
    print(f"✅ File server files: {len(file_links) if file_links else 'Access restricted'}")
    print("=" * 60)
    
    print("\n🎯 KEY INSIGHTS:")
    print("1. Product pages contain direct PDF links to technical documents")
    print("2. Category pages list multiple products with their own documents")
    print("3. File server may require direct links (not browsable)")
    print("4. Each product has multiple technical documents (datasheets, guides, etc.)")

if __name__ == "__main__":
    asyncio.run(main()) 