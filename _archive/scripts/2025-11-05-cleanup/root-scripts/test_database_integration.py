#!/usr/bin/env python3
"""
Database Integration Test Script

This script tests the database integration by:
1. Creating a manufacturer (ROCKWOOL)
2. Creating sample categories
3. Creating sample products from our scraped PDFs
4. Verifying the data was inserted correctly
"""

import requests
import json
import os
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"
PDF_DIR = Path("src/downloads/rockwool_datasheets")

class DatabaseIntegrationTest:
    def __init__(self):
        self.api_base = API_BASE_URL
        self.manufacturer_id = None
        self.category_id = None
        
    def test_api_health(self):
        """Test API connectivity"""
        try:
            response = requests.get(f"{self.api_base}/health")
            print(f"✅ API Health: {response.status_code}")
            print(f"   Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ API Health failed: {e}")
            return False
    
    def create_manufacturer(self):
        """Create or find ROCKWOOL manufacturer"""
        try:
            # First check if ROCKWOOL manufacturer already exists
            response = requests.get(f"{self.api_base}/manufacturers")
            if response.status_code == 200:
                manufacturers = response.json()
                for mfr in manufacturers:
                    if mfr['name'] == 'ROCKWOOL':
                        self.manufacturer_id = mfr['id']
                        print(f"✅ Found existing manufacturer: ID {self.manufacturer_id}")
                        return True
            
            # If not found, create new one
            data = {
                "name": "ROCKWOOL",
                "description": "ROCKWOOL Group dán anyacég magyar leányvállalata, kőzetgyapot alapú szigetelőanyagok gyártója",
                "website": "https://www.rockwool.hu",
                "country": "Dánia"
            }
            response = requests.post(
                f"{self.api_base}/manufacturers",
                params=data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.manufacturer_id = result['id']
                print(f"✅ Manufacturer created: ID {self.manufacturer_id}")
                return True
            else:
                print(f"❌ Manufacturer creation failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Manufacturer creation error: {e}")
            return False
    
    def create_category(self):
        """Create sample category"""
        try:
            data = {
                "name": "Tetőszigetelés",
                "description": "Tetők hő- és hangszigetelésére szolgáló termékek"
            }
            response = requests.post(
                f"{self.api_base}/categories",
                params=data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.category_id = result['id']
                print(f"✅ Category created: ID {self.category_id}")
                return True
            else:
                print(f"❌ Category creation failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Category creation error: {e}")
            return False
    
    def create_sample_product(self, pdf_name):
        """Create a product from PDF filename with proper UTF-8 handling"""
        try:
            # FIXED: Proper UTF-8 decoding for Hungarian characters
            product_name = pdf_name.replace('termxE9kadatlap.pdf', ' termékadatlap')
            product_name = product_name.replace('.pdf', '')
            # Fix common encoding issues
            product_name = (product_name.replace('xE9', 'é')
                           .replace('x151', 'ő') 
                           .replace('xF3', 'ó')
                           .replace('xE1', 'á')
                           .replace('xF6', 'ö')
                           .replace('xFC', 'ü')
                           .replace('xED', 'í')
                           .replace('xFA', 'ú'))
            
            data = {
                "name": f"ROCKWOOL {product_name}",
                "description": f"Kőzetgyapot szigetelőanyag - {product_name}",
                "manufacturer_id": self.manufacturer_id,
                "category_id": self.category_id,
                "technical_specs": {
                    "material": "kőzetgyapot",
                    "application": "építőanyag szigetelés",
                    "source_pdf": pdf_name
                }
            }
            
            response = requests.post(
                f"{self.api_base}/products",
                params=data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Product created: {result['name']} (ID: {result['id']})")
                return result['id']
            else:
                print(f"❌ Product creation failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Product creation error: {e}")
            return None
    
    def verify_data(self):
        """Verify data was inserted correctly"""
        try:
            # Check manufacturers
            response = requests.get(f"{self.api_base}/manufacturers")
            manufacturers = response.json()
            print(f"✅ Manufacturers in DB: {len(manufacturers)}")
            
            # Check categories
            response = requests.get(f"{self.api_base}/categories")
            categories = response.json()
            print(f"✅ Categories in DB: {len(categories)}")
            
            # Check products
            response = requests.get(f"{self.api_base}/products")
            products = response.json()
            print(f"✅ Products in DB: {len(products)}")
            
            return len(manufacturers) > 0 and len(categories) > 0 and len(products) > 0
            
        except Exception as e:
            print(f"❌ Data verification error: {e}")
            return False
    
    def run_test(self):
        """Run the complete integration test"""
        print("🎯 Starting Database Integration Test")
        print("=" * 50)
        
        # Step 1: Test API Health
        if not self.test_api_health():
            print("❌ Test failed: API not healthy")
            return False
        
        # Step 2: Create manufacturer
        if not self.create_manufacturer():
            print("❌ Test failed: Could not create manufacturer")
            return False
        
        # Step 3: Create category
        if not self.create_category():
            print("❌ Test failed: Could not create category")
            return False
        
        # Step 4: Create ALL products from PDFs (PRODUCTION MODE)
        pdf_files = list(PDF_DIR.glob("*.pdf"))
        print(f"📁 Processing ALL {len(pdf_files)} PDFs in PRODUCTION mode...")
        
        created_products = 0
        for pdf_file in pdf_files:
            if self.create_sample_product(pdf_file.name):
                created_products += 1
        
        print(f"✅ Created {created_products} products")
        
        # Step 5: Verify data
        if not self.verify_data():
            print("❌ Test failed: Data verification failed")
            return False
        
        print("\n🎉 Database Integration Test SUCCESSFUL!")
        print("=" * 50)
        return True

if __name__ == "__main__":
    test = DatabaseIntegrationTest()
    success = test.run_test()
    
    if success:
        print("\n✅ Next steps: Ready for full PDF processing!")
    else:
        print("\n❌ Test failed. Check API and database connectivity.") 