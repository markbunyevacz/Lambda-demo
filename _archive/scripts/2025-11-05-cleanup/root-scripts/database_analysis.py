#!/usr/bin/env python3
"""
Database Content Analysis - What's Actually Stored vs Source PDFs

This script analyzes the discrepancy between what should be in the database
vs what's actually stored.
"""

import requests
import os
from pathlib import Path

API_BASE_URL = "http://localhost:8000"
PDF_DIR = Path("src/downloads")

def analyze_database_content():
    """Analyze current database content"""
    print("🔍 DATABASE CONTENT ANALYSIS")
    print("=" * 80)
    
    # Get database content
    try:
        products_response = requests.get(f"{API_BASE_URL}/products")
        categories_response = requests.get(f"{API_BASE_URL}/categories")
        manufacturers_response = requests.get(f"{API_BASE_URL}/manufacturers")
        
        products = products_response.json()
        categories = categories_response.json()
        manufacturers = manufacturers_response.json()
        
        print("📊 Database Summary:")
        print(f"   🏭 Manufacturers: {len(manufacturers)}")
        print(f"   📁 Categories: {len(categories)}")
        print(f"   📦 Products: {len(products)}")
        
        # Analyze issues
        print("\n❌ ISSUES IDENTIFIED:")
        
        # Check technical specs
        empty_specs = [p for p in products if not p['technical_specs']]
        print(f"   📋 Products with empty technical_specs: "
              f"{len(empty_specs)}/{len(products)}")
        
        # Check prices
        no_prices = [p for p in products if p['price'] is None]
        print(f"   💰 Products with no prices: "
              f"{len(no_prices)}/{len(products)}")
        
        # Check source tracking
        no_source = [p for p in products if not p.get('source_url')]
        print(f"   🔗 Products with no source URL: "
              f"{len(no_source)}/{len(products)}")
        
        print("\n📁 CATEGORY BREAKDOWN:")
        category_counts = {}
        for product in products:
            cat_name = product['category']['name']
            category_counts[cat_name] = category_counts.get(cat_name, 0) + 1
        
        for cat_name, count in sorted(category_counts.items()):
            print(f"   📂 {cat_name}: {count} products")
        
        return products, categories, manufacturers
        
    except Exception as e:
        print(f"❌ Error accessing database: {e}")
        return None, None, None

def analyze_source_files():
    """Analyze source PDF files"""
    print("\n📄 SOURCE FILES ANALYSIS")
    print("=" * 80)
    
    pdf_files = list(PDF_DIR.glob("*.pdf"))
    print(f"📄 Total PDF Files: {len(pdf_files)}")
    
    # Categorize files
    categories = {
        "Tetőszigetelés": [],
        "Homlokzati hőszigetelés": [],
        "Padlószigetelés": [],
        "Válaszfal szigetelés": [],
        "Gépészeti szigetelés": [],
        "Tűzvédelem": [],
        "Egyéb": []
    }
    
    for pdf_file in pdf_files:
        filename_lower = pdf_file.name.lower()
        size_mb = round(pdf_file.stat().st_size / (1024 * 1024), 2)
        
        roof_keywords = ['roofrock', 'deltarock', 'dachrock', 'durock', 
                        'steelrock']
        facade_keywords = ['frontrock', 'fixrock', 'multirock']
        mech_keywords = ['klimarock', 'techrock', 'rockwool-800']
        fire_keywords = ['conlit', 'firerock']
        
        if any(x in filename_lower for x in roof_keywords):
            categories["Tetőszigetelés"].append((pdf_file.name, size_mb))
        elif any(x in filename_lower for x in facade_keywords):
            categories["Homlokzati hőszigetelés"].append(
                (pdf_file.name, size_mb))
        elif any(x in filename_lower for x in ['steprock']):
            categories["Padlószigetelés"].append((pdf_file.name, size_mb))
        elif any(x in filename_lower for x in ['airrock']):
            categories["Válaszfal szigetelés"].append(
                (pdf_file.name, size_mb))
        elif any(x in filename_lower for x in mech_keywords):
            categories["Gépészeti szigetelés"].append(
                (pdf_file.name, size_mb))
        elif any(x in filename_lower for x in fire_keywords):
            categories["Tűzvédelem"].append((pdf_file.name, size_mb))
        else:
            categories["Egyéb"].append((pdf_file.name, size_mb))
    
    print("\n📂 SOURCE FILES BY CATEGORY:")
    for cat_name, files in categories.items():
        print(f"   📁 {cat_name}: {len(files)} files")
        for filename, size_mb in sorted(files)[:3]:  # Show first 3
            print(f"      • {filename} ({size_mb} MB)")
        if len(files) > 3:
            print(f"      ... and {len(files) - 3} more")
    
    return categories

def show_sample_products_with_issues(products):
    """Show sample products highlighting the issues"""
    print(f"\n🔍 SAMPLE PRODUCTS WITH ISSUES:")
    print("=" * 80)
    
    for i, product in enumerate(products[:5]):
        print(f"\n📦 Product {i+1}: {product['name']}")
        print(f"   🆔 ID: {product['id']}")
        print(f"   📁 Category: {product['category']['name']}")
        print(f"   💰 Price: {product['price']} {product['currency']}")
        print(f"   📋 Technical Specs: {product['technical_specs']}")
        print(f"   🔗 Source URL: {product['source_url']}")
        print(f"   ⚠️  ISSUES:")
        
        issues = []
        if not product['technical_specs']:
            issues.append("Empty technical specifications")
        if product['price'] is None:
            issues.append("No price information")
        if not product['source_url']:
            issues.append("No source PDF link")
        
        for issue in issues:
            print(f"      ❌ {issue}")

def generate_fix_recommendations():
    """Generate recommendations to fix the issues"""
    print(f"\n🔧 RECOMMENDED FIXES:")
    print("=" * 80)
    
    print(f"1. 📋 **Technical Specifications Missing**")
    print(f"   • Problem: All products have empty technical_specs {{}}")
    print(f"   • Fix: Re-run database integration with proper technical specs mapping")
    print(f"   • Should include: file_size, source_pdf, material_type, scraped_date")
    
    print(f"\n2. 💰 **Price Information Missing**")
    print(f"   • Problem: All products have price = null")
    print(f"   • Fix: Extract price data from PDF content or connect to ROCKWOOL price API")
    print(f"   • Alternative: Mark as 'Contact for pricing' with flag")
    
    print(f"\n3. 🔗 **Source PDF Links Missing**") 
    print(f"   • Problem: No source_url pointing to original PDFs")
    print(f"   • Fix: Add file:// links or web links to PDF locations")
    print(f"   • Should enable: Direct access to original documents")
    
    print(f"\n4. 📄 **Detailed Technical Data Missing**")
    print(f"   • Problem: No extracted technical specifications from PDFs")
    print(f"   • Fix: Implement PDF text extraction and parsing")
    print(f"   • Should extract: R-values, dimensions, fire ratings, etc.")

def main():
    """Main analysis function"""
    
    # Analyze current database
    products, categories, manufacturers = analyze_database_content()
    
    if products:
        # Analyze source files
        source_categories = analyze_source_files()
        
        # Show sample issues
        show_sample_products_with_issues(products)
        
        # Generate fix recommendations
        generate_fix_recommendations()
        
        print(f"\n✅ SUMMARY:")
        print(f"   📊 Database has {len(products)} products from {len(source_categories)} file categories")
        print(f"   ⚠️  Major issues: Missing technical specs, prices, and PDF links")
        print(f"   🎯 Next priority: Fix database integration to include complete data")

if __name__ == "__main__":
    main() 