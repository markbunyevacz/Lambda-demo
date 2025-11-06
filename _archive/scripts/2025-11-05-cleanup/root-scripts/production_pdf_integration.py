#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRODUCTION PDF Integration Script
=================================

Processes ALL scraped ROCKWOOL PDFs into database with proper UTF-8 handling.
This is the REAL production script - no simulations, no tests.
"""

import os
import sys
import logging
from pathlib import Path
import requests
import json
from urllib.parse import quote

# Add backend modules for duplicate prevention
sys.path.append(str(Path(__file__).parent / "src" / "backend"))
from app.duplicate_prevention import DuplicatePreventionManager
from app.database import get_db

# Ensure UTF-8 encoding
if sys.stdout.encoding != 'utf-8':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configure logging with UTF-8
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ProductionPDFProcessor:
    """Real production PDF processor for Lambda.hu"""
    
    def __init__(self):
        self.api_base = "http://localhost:8000"
        self.pdf_dir = Path("src/downloads/rockwool_datasheets")
        self.stats = {
            'processed': 0,
            'successful': 0, 
            'failed': 0,
            'skipped': 0,
            'duplicates_prevented': 0
        }
        # Initialize duplicate prevention
        try:
            self.db = next(get_db())
            self.duplicate_manager = DuplicatePreventionManager(self.db)
        except Exception as e:
            logger.warning(f"⚠️  Could not initialize duplicate prevention: {e}")
            self.duplicate_manager = None
        
    def fix_encoding(self, text: str) -> str:
        """Fix common URL encoding issues in filenames"""
        replacements = {
            'xE9': 'é',  # termékadatlap
            'x151': 'ő',  # hőszigetelő
            'xF3': 'ó',   # hővezetési
            'xE1': 'á',   # árlista
            'xF6': 'ö',   # hőmérséklet
            'xFC': 'ü',   # tűzvédelem
            'xED': 'í',   # szigetelési
            'xFA': 'ú',   # műszaki
            'x171': 'ű',  # tűzállósági
            'termxE9kadatlap': 'termékadatlap'
        }
        
        result = text
        for encoded, decoded in replacements.items():
            result = result.replace(encoded, decoded)
        
        return result.strip()
    
    def extract_product_name(self, filename: str) -> str:
        """Extract clean product name from filename"""
        name = filename.replace('.pdf', '')
        name = self.fix_encoding(name)
        
        # Remove common suffixes
        suffixes_to_remove = [
            'termékadatlap',
            'és tervezési segédlet',
            'SZAKI ADATLAP'
        ]
        
        for suffix in suffixes_to_remove:
            if suffix in name:
                name = name.replace(suffix, '').strip()
        
        # Clean up spacing
        name = ' '.join(name.split())
        
        return name
    
    def check_api_health(self) -> bool:
        """Check if API is running"""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ API health check failed: {e}")
            return False
    
    def create_manufacturer(self) -> int:
        """Create or get ROCKWOOL manufacturer"""
        try:
            # Check if exists
            response = requests.get(f"{self.api_base}/manufacturers")
            if response.status_code == 200:
                manufacturers = response.json()
                for mfr in manufacturers:
                    if mfr['name'] == 'ROCKWOOL':
                        logger.info(f"✅ Found existing manufacturer: {mfr['name']}")
                        return mfr['id']
            
            # Create new
            data = {
                "name": "ROCKWOOL",
                "description": "ROCKWOOL Group dán anyacég magyar leányvállalata",
                "website": "https://www.rockwool.hu",
                "country": "Dánia"
            }
            
            response = requests.post(f"{self.api_base}/manufacturers", params=data)
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Created manufacturer: {result['name']}")
                return result['id']
            else:
                logger.error(f"❌ Failed to create manufacturer: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Manufacturer error: {e}")
            return None
    
    def get_or_create_category(self, category_name: str) -> int:
        """Get or create product category"""
        try:
            # Check if exists
            response = requests.get(f"{self.api_base}/categories")
            if response.status_code == 200:
                categories = response.json()
                for cat in categories:
                    if cat['name'] == category_name:
                        return cat['id']
            
            # Create new
            data = {
                "name": category_name,
                "description": f"ROCKWOOL {category_name} termékek"
            }
            
            response = requests.post(f"{self.api_base}/categories", params=data)
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Created category: {result['name']}")
                return result['id']
            else:
                logger.error(f"❌ Failed to create category: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Category error: {e}")
            return None
    
    def determine_category(self, product_name: str) -> str:
        """Determine product category from name"""
        name_lower = product_name.lower()
        
        if any(term in name_lower for term in ['roofrock', 'dachrock', 'steelrock']):
            return 'Tetőszigetelés'
        elif any(term in name_lower for term in ['frontrock', 'fixrock']):
            return 'Homlokzati hőszigetelés'
        elif any(term in name_lower for term in ['airrock', 'deltarock']):
            return 'Válaszfal szigetelés'
        elif any(term in name_lower for term in ['steprock', 'stroprock']):
            return 'Padló és födém szigetelés'
        elif any(term in name_lower for term in ['conlit', 'firerock']):
            return 'Tűzvédelem'
        elif any(term in name_lower for term in ['klimarock', 'klimafix', 'klimamat']):
            return 'Gépészeti szigetelés'
        elif any(term in name_lower for term in ['multirock', 'ceilingrock']):
            return 'Magastető és tetőtér'
        else:
            return 'Építőipari szigetelés'
    
    def create_product(self, pdf_file: Path, manufacturer_id: int) -> bool:
        """Create product from PDF file with duplicate prevention"""
        try:
            # Extract product info
            product_name = self.extract_product_name(pdf_file.name)
            category_name = self.determine_category(product_name)
            
            # Get category ID
            category_id = self.get_or_create_category(category_name)
            if not category_id:
                logger.error(f"❌ Could not create category for {product_name}")
                return False
            
            full_product_name = f"ROCKWOOL {product_name}"
            
            # DUPLICATE PREVENTION: Check if product already exists
            if self.duplicate_manager:
                existing = self.duplicate_manager.check_existing_product(
                    name=full_product_name,
                    manufacturer_id=manufacturer_id,
                    source_url=f"file://{pdf_file.name}"
                )
                
                if existing:
                    logger.info(f"⏭️  Skipping duplicate: {full_product_name} (ID: {existing.id})")
                    self.stats['duplicates_prevented'] += 1
                    return True  # Not an error, just prevented duplicate
            
            # Prepare product data with proper UTF-8 encoding
            data = {
                "name": full_product_name,
                "description": f"Kőzetgyapot szigetelőanyag - {product_name}",
                "manufacturer_id": manufacturer_id,
                "category_id": category_id,
                "source_url": f"file://{pdf_file.name}",
                "technical_specs": json.dumps({
                    "material": "kőzetgyapot",
                    "application": "építőipari szigetelés",
                    "source_pdf": pdf_file.name,
                    "file_size": pdf_file.stat().st_size
                }, ensure_ascii=False)
            }
            
            # Use duplicate-safe creation if available
            if self.duplicate_manager:
                try:
                    product = self.duplicate_manager.safe_create_product(data)
                    logger.info(f"✅ Created product: {product.name} (ID: {product.id})")
                    return True
                except Exception as e:
                    logger.warning(f"⚠️  Duplicate manager failed, using API: {e}")
            
            # Fallback to API creation
            response = requests.post(
                f"{self.api_base}/products", 
                params=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Created product: {result['name']} (ID: {result['id']})")
                return True
            else:
                logger.error(f"❌ Product creation failed: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Product creation error: {e}")
            return False
    
    def process_all_pdfs(self):
        """Process all PDFs in the download directory"""
        
        print("🚀 PRODUCTION PDF INTEGRATION - LAMBDA.HU")
        print("=" * 60)
        
        # Check API
        if not self.check_api_health():
            print("❌ API not available. Please start the backend service.")
            return False
        
        # Get manufacturer
        manufacturer_id = self.create_manufacturer()
        if not manufacturer_id:
            print("❌ Could not create/find manufacturer")
            return False
        
        # Get all PDF files
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        if not pdf_files:
            print(f"❌ No PDF files found in {self.pdf_dir}")
            return False
        
        print(f"📄 Found {len(pdf_files)} PDF files")
        print(f"🎯 Processing ALL files in PRODUCTION mode")
        print("=" * 60)
        
        # Process each PDF
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n📄 Processing ({i}/{len(pdf_files)}): {pdf_file.name}")
            
            self.stats['processed'] += 1
            
            if self.create_product(pdf_file, manufacturer_id):
                self.stats['successful'] += 1
            else:
                self.stats['failed'] += 1
        
        # Print final statistics
        print("\n" + "=" * 60)
        print("🏁 PRODUCTION INTEGRATION COMPLETE")
        print("=" * 60)
        print(f"📊 Processing Results:")
        print(f"   📄 PDFs processed: {self.stats['processed']}")
        print(f"   ✅ Successfully created: {self.stats['successful']}")
        print(f"   ⏭️  Duplicates prevented: {self.stats['duplicates_prevented']}")
        print(f"   ❌ Failed: {self.stats['failed']}")
        
        total_processed = self.stats['successful'] + self.stats['duplicates_prevented']
        if total_processed > 0:
            print(f"\n🎉 SUCCESS: {total_processed} ROCKWOOL products processed!")
            print(f"   📦 New products: {self.stats['successful']}")
            print(f"   🛡️  Duplicates avoided: {self.stats['duplicates_prevented']}")
            print("✅ API endpoints ready: http://localhost:8000/products")
            print("✅ Ready for vector database integration")
        
        return self.stats['successful'] > 0

def main():
    """Main production pipeline"""
    # Set UTF-8 environment
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    processor = ProductionPDFProcessor()
    success = processor.process_all_pdfs()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 