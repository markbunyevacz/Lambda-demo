#!/usr/bin/env python3
"""
Real Database Integration Demo - ROCKWOOL Products

This demo processes our actual scraped ROCKWOOL PDFs and inserts them 
as real products into the PostgreSQL database.

Data: 57 ROCKWOOL product datasheets from Hungary
Target: Production PostgreSQL database via FastAPI
"""

import requests
import os
from pathlib import Path
import re

# Configuration
API_BASE_URL = "http://localhost:8000"
PDF_DIR = Path("src/downloads")

class RockwoolDatabaseDemo:
    def __init__(self):
        self.api_base = API_BASE_URL
        self.manufacturer_id = None
        self.categories = {}
        
    def verify_api_connection(self):
        """Verify API is running"""
        try:
            response = requests.get(f"{self.api_base}/health")
            health = response.json()
            print(f"🔗 API Status: {health['status']}")
            print(f"🗄️  Database: {health['database']}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ API connection failed: {e}")
            return False
    
    def setup_manufacturer(self):
        """Setup ROCKWOOL manufacturer"""
        try:
            # Check existing manufacturers
            response = requests.get(f"{self.api_base}/manufacturers")
            if response.status_code == 200:
                manufacturers = response.json()
                for mfr in manufacturers:
                    if mfr['name'] == 'ROCKWOOL':
                        self.manufacturer_id = mfr['id']
                        print(f"🏭 Using existing ROCKWOOL: ID {self.manufacturer_id}")
                        return True
            
            # Create ROCKWOOL manufacturer
            data = {
                "name": "ROCKWOOL",
                "description": "ROCKWOOL Group - kőzetgyapot szigetelőanyagok világpiacvezetője",
                "website": "https://www.rockwool.hu",
                "country": "Dánia"
            }
            response = requests.post(f"{self.api_base}/manufacturers", params=data)
            
            if response.status_code == 200:
                result = response.json()
                self.manufacturer_id = result['id']
                print(f"🏭 Created ROCKWOOL manufacturer: ID {self.manufacturer_id}")
                return True
            else:
                print(f"❌ Failed to create manufacturer: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Manufacturer setup error: {e}")
            return False
    
    def setup_categories(self):
        """Setup real ROCKWOOL product categories"""
        categories_to_create = [
            {
                "name": "Tetőszigetelés",
                "description": "Tetők hő- és hangszigetelésére szolgáló termékek (Roofrock, Deltarock, Dachrock)"
            },
            {
                "name": "Homlokzati hőszigetelés", 
                "description": "Épülethomlokzatok külső hőszigetelésére alkalmas termékek (Frontrock, Fixrock)"
            },
            {
                "name": "Padlószigetelés",
                "description": "Padlószerkezetek hő- és hangszigetelő anyagai (Steprock)"
            },
            {
                "name": "Válaszfal szigetelés",
                "description": "Belső válaszfalak szigetelésére szolgáló termékek (Airrock)"
            },
            {
                "name": "Gépészeti szigetelés",
                "description": "Gépészeti rendszerek, csővezetékek szigetelése (Klimarock, Techrock)"
            },
            {
                "name": "Tűzvédelem",
                "description": "Tűzálló és tűzgátló építőanyagok (Conlit, Firerock)"
            }
        ]
        
        print(f"📁 Creating {len(categories_to_create)} product categories...")
        
        for cat_data in categories_to_create:
            try:
                response = requests.post(f"{self.api_base}/categories", params=cat_data)
                if response.status_code == 200:
                    result = response.json()
                    self.categories[cat_data['name']] = result['id']
                    print(f"  ✅ {cat_data['name']}: ID {result['id']}")
                else:
                    print(f"  ❌ Failed to create {cat_data['name']}: {response.status_code}")
            except Exception as e:
                print(f"  ❌ Error creating {cat_data['name']}: {e}")
        
        return len(self.categories) > 0
    
    def categorize_product(self, filename):
        """Categorize product based on filename"""
        filename_lower = filename.lower()
        
        if any(x in filename_lower for x in ['roofrock', 'deltarock', 'dachrock', 'durock', 'steelrock']):
            return "Tetőszigetelés"
        elif any(x in filename_lower for x in ['frontrock', 'fixrock', 'multirock']):
            return "Homlokzati hőszigetelés"
        elif any(x in filename_lower for x in ['steprock', 'stoprock']):
            return "Padlószigetelés"
        elif any(x in filename_lower for x in ['airrock']):
            return "Válaszfal szigetelés"
        elif any(x in filename_lower for x in ['klimarock', 'techrock', 'rockwool-800']):
            return "Gépészeti szigetelés"
        elif any(x in filename_lower for x in ['conlit', 'firerock']):
            return "Tűzvédelem"
        else:
            return "Tetőszigetelés"  # Default category
    
    def clean_product_name(self, filename):
        """Extract clean product name from PDF filename"""
        # Remove file extension
        name = filename.replace('.pdf', '')
        
        # Remove common suffixes
        name = re.sub(r'termxE9kadatlap.*', '', name)
        name = re.sub(r'xE9s.*', '', name)
        
        # Fix encoding issues
        name = name.replace('xE9', 'é')
        name = name.replace('x151', 'ő')
        name = name.replace('xF3', 'ó')
        name = name.replace('xE1', 'á')
        
        # Clean up
        name = name.strip()
        name = re.sub(r'\s+', ' ', name)
        
        # Capitalize first letter
        if name:
            name = name[0].upper() + name[1:]
        
        return name
    
    def process_pdf_files(self):
        """Process all scraped PDF files and create products"""
        pdf_files = list(PDF_DIR.glob("*.pdf"))
        print(f"📄 Processing {len(pdf_files)} PDF files...")
        
        created_count = 0
        skipped_count = 0
        
        for pdf_file in pdf_files:
            try:
                # Extract product info
                product_name = self.clean_product_name(pdf_file.name)
                category_name = self.categorize_product(pdf_file.name)
                category_id = self.categories.get(category_name)
                
                if not category_id:
                    print(f"  ⚠️  Skipping {pdf_file.name}: No category found")
                    skipped_count += 1
                    continue
                
                # Create product
                product_data = {
                    "name": f"ROCKWOOL {product_name}",
                    "description": f"Kőzetgyapot szigetelőanyag - {product_name}",
                    "manufacturer_id": self.manufacturer_id,
                    "category_id": category_id,
                    "technical_specs": {
                        "material": "kőzetgyapot",
                        "brand": "ROCKWOOL",
                        "category": category_name,
                        "source_pdf": pdf_file.name,
                        "file_size": pdf_file.stat().st_size,
                        "scraped_date": "2025-06-30"
                    }
                }
                
                response = requests.post(f"{self.api_base}/products", params=product_data)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"  ✅ {product_name} → {category_name} (ID: {result['id']})")
                    created_count += 1
                else:
                    print(f"  ❌ Failed to create {product_name}: {response.status_code}")
                    skipped_count += 1
                    
            except Exception as e:
                print(f"  ❌ Error processing {pdf_file.name}: {e}")
                skipped_count += 1
        
        return created_count, skipped_count
    
    def verify_results(self):
        """Verify integration results"""
        try:
            # Get counts
            manufacturers = requests.get(f"{self.api_base}/manufacturers").json()
            categories = requests.get(f"{self.api_base}/categories").json()  
            products = requests.get(f"{self.api_base}/products").json()
            
            print(f"\n📊 Database Integration Results:")
            print(f"🏭 Manufacturers: {len(manufacturers)}")
            print(f"📁 Categories: {len(categories)}")
            print(f"📦 Products: {len(products)}")
            
            # Show sample products
            if products:
                print(f"\n📋 Sample Products:")
                for product in products[:5]:
                    print(f"  • {product['name']} (ID: {product['id']})")
                if len(products) > 5:
                    print(f"  ... and {len(products) - 5} more")
            
            return len(products) > 0
            
        except Exception as e:
            print(f"❌ Verification error: {e}")
            return False
    
    def run_demo(self):
        """Run the complete database integration demo"""
        print("🎯 ROCKWOOL Database Integration Demo")
        print("=" * 60)
        
        # Step 1: Verify API
        if not self.verify_api_connection():
            print("❌ Demo failed: API not available")
            return False
        
        # Step 2: Setup manufacturer
        if not self.setup_manufacturer():
            print("❌ Demo failed: Could not setup manufacturer")
            return False
        
        # Step 3: Setup categories
        if not self.setup_categories():
            print("❌ Demo failed: Could not setup categories")
            return False
        
        # Step 4: Process real PDF data
        created, skipped = self.process_pdf_files()
        print(f"\n📊 Processing Results: ✅ {created} created, ⚠️ {skipped} skipped")
        
        # Step 5: Verify results
        if not self.verify_results():
            print("❌ Demo failed: Data verification failed")
            return False
        
        print(f"\n🎉 ROCKWOOL Database Integration Demo COMPLETE!")
        print("=" * 60)
        print("✅ Real ROCKWOOL products successfully integrated into PostgreSQL")
        print("🔗 Access via: http://localhost:8000/products")
        
        return True

if __name__ == "__main__":
    demo = RockwoolDatabaseDemo()
    success = demo.run_demo()
    
    if success:
        print(f"\n🚀 Next Steps:")
        print(f"   • View products: http://localhost:8000/products")
        print(f"   • API docs: http://localhost:8000/docs") 
        print(f"   • Ready for UI integration!")
    else:
        print(f"\n❌ Demo failed. Check database connectivity.") 