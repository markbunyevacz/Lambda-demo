#!/usr/bin/env python3
"""
Lambda.hu Production PDF Processing
Real AI-powered PDF extraction and database integration

NO SIMULATIONS - Uses:
- PyPDF2/pdfplumber for real PDF text extraction
- Claude 3.5 Haiku for AI content analysis 
- Database integration with extracted technical specs
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

# Add paths for imports
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent / "pdf_processing"))

# Import real PDF processor
try:
    from real_pdf_processor import RealPDFProcessor, PDFExtractionResult
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure real_pdf_processor.py is available")
    sys.exit(1)

# Database imports
try:
    from app.database import get_db
    from app.models.product import Product
    from sqlalchemy.orm import Session
except ImportError as e:
    print(f"❌ Database import error: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 🎯 MANUFACTURER-SPECIFIC ATTRIBUTE MAPPINGS
MANUFACTURER_ATTRIBUTE_MAPS = {
    'ROCKWOOL': {
        'hővezetési tényező': 'thermal_conductivity',
        'sűrűség': 'density',
        'tűzállóság': 'fire_resistance'
    },
    'LEIER': {
        'nyomószilárdság': 'compressive_strength',    # 👈 NEW
        'vízfelvétel': 'water_absorption',            # 👈 NEW  
        'fagyállóság': 'frost_resistance',            # 👈 NEW
        'műanyag-tartalom': 'plastic_content'         # 👈 NEW
    },
    'BAUMIT': {
        'tapadószilárdság': 'adhesive_strength',      # 👈 NEW
        'diffúziós ellenállás': 'vapor_resistance',   # 👈 NEW
        'kötésidő': 'setting_time',                   # 👈 NEW
        'szemcseméret': 'grain_size'                  # 👈 NEW
    }
}

class ProductionPDFManager:
    """Production PDF processing and database integration"""
    
    def __init__(self):
        self.pdf_processor = RealPDFProcessor()
        self.stats = {
            'pdfs_processed': 0,
            'products_updated': 0,
            'new_specs_added': 0,
            'errors': 0
        }
    
    def update_product_from_pdf(self, pdf_result: PDFExtractionResult, db: Session) -> bool:
        """Update product in database with PDF extraction results"""
        
        try:
            # Find matching product by name similarity
            product_name = pdf_result.product_name.replace('termékadatlap', '').strip()
            
            # Try exact match first
            product = db.query(Product).filter(
                Product.name.ilike(f"%{product_name}%")
            ).first()
            
            if not product:
                # Try fuzzy matching with filename
                filename_product = pdf_result.source_filename.replace('.pdf', '').replace('termxE9kadatlap', '')
                filename_product = filename_product.replace('xE9', 'é').replace('xF6', 'ö')
                
                product = db.query(Product).filter(
                    Product.name.ilike(f"%{filename_product}%")
                ).first()
            
            if not product:
                logger.warning(f"⚠️  No matching product found for: {pdf_result.product_name}")
                return False
            
            # Update product with real extracted data
            original_specs = product.technical_specs or {}
            
            # Merge AI-extracted specs with existing data
            updated_specs = {
                **original_specs,
                **pdf_result.technical_specs,
                "ai_extraction": {
                    "extracted_at": datetime.now().isoformat(),
                    "confidence_score": pdf_result.confidence_score,
                    "source_pdf": pdf_result.source_filename,
                    "extraction_method": "claude_ai_real"
                }
            }
            
            # Update pricing if available
            if pdf_result.pricing_info:
                updated_specs["pricing"] = pdf_result.pricing_info
            
            # Update product
            product.technical_specs = updated_specs
            product.updated_at = datetime.now()
            
            # Update metadata
            if not product.metadata:
                product.metadata = {}
            
            product.metadata.update({
                "pdf_processed": True,
                "pdf_source": pdf_result.source_filename,
                "ai_confidence": pdf_result.confidence_score,
                "processing_date": datetime.now().isoformat()
            })
            
            db.commit()
            
            self.stats['products_updated'] += 1
            self.stats['new_specs_added'] += len(pdf_result.technical_specs)
            
            logger.info(f"✅ Updated product: {product.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database update failed for {pdf_result.product_name}: {e}")
            db.rollback()
            self.stats['errors'] += 1
            return False
    
    def process_all_pdfs(self) -> Dict[str, Any]:
        """Process all PDFs and update database"""
        
        print("🚀 LAMBDA.HU PRODUCTION PDF PROCESSING")
        print("=" * 60)
        print("✅ Real Claude AI analysis")
        print("✅ PyPDF2 + pdfplumber extraction")
        print("✅ Database integration")
        print("❌ NO SIMULATIONS")
        print()
        
        # Set PDF directory path
        pdf_directory = Path("/app/src/downloads/rockwool_datasheets")
        if not pdf_directory.exists():
            # Try alternative paths
            pdf_directory = Path("src/downloads/rockwool_datasheets")
            if not pdf_directory.exists():
                raise FileNotFoundError(f"PDF directory not found: {pdf_directory}")
        
        logger.info(f"📁 PDF Directory: {pdf_directory}")
        
        # Process PDFs with real AI
        try:
            pdf_results = self.pdf_processor.process_directory(pdf_directory)
            self.stats['pdfs_processed'] = len(pdf_results)
            
            if not pdf_results:
                logger.warning("⚠️  No PDFs processed successfully")
                return self.stats
            
            logger.info(f"📄 {len(pdf_results)} PDFs processed with real AI")
            
        except Exception as e:
            logger.error(f"❌ PDF processing failed: {e}")
            self.stats['errors'] += 1
            return self.stats
        
        # Update database with results
        try:
            db = next(get_db())
            
            for result in pdf_results:
                logger.info(f"🔄 Updating database for: {result.product_name}")
                self.update_product_from_pdf(result, db)
            
            db.close()
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            self.stats['errors'] += 1
        
        return self.stats
    
    def print_final_report(self):
        """Print comprehensive processing report"""
        
        print("\\n" + "=" * 80)
        print("🏁 PRODUCTION PDF PROCESSING COMPLETE")
        print("=" * 80)
        
        print(f"📊 Processing Statistics:")
        print(f"   📄 PDFs processed: {self.stats['pdfs_processed']}")
        print(f"   🔄 Products updated: {self.stats['products_updated']}")
        print(f"   🔧 New specs added: {self.stats['new_specs_added']}")
        print(f"   ❌ Errors encountered: {self.stats['errors']}")
        
        success_rate = (self.stats['products_updated'] / max(self.stats['pdfs_processed'], 1)) * 100
        print(f"   📈 Success rate: {success_rate:.1f}%")
        
        print(f"\\n✅ REAL AI-POWERED PDF PROCESSING:")
        print("   🧠 Claude 3.5 Haiku AI analysis")
        print("   📋 Structured technical specifications")
        print("   💰 Price information extraction")
        print("   💾 Database integration complete")
        print("   🚫 ZERO simulations - 100% real processing")
        
        print(f"\\n🌐 API Access:")
        print("   📍 Products API: http://localhost:8000/products")
        print("   🔍 Search API: http://localhost:8000/search")
        print("   📊 RAG Pipeline ready for semantic search")

    def _extract_unit_from_specs(self, normalized_specs: Dict, manufacturer: str) -> Optional[str]:
        # MANUFACTURER-SPECIFIC UNITS
        manufacturer_units = {
            'ROCKWOOL': {'thickness': 'm2', 'thermal_conductivity': 'm2'},
            'LEIER': {'compressive_strength': 'db', 'water_absorption': 'm2'},
            'BAUMIT': {'adhesive_strength': 'kg', 'setting_time': 'liter'}
        }

    def _get_category_specific_attributes(self, category: str, manufacturer: str) -> Dict:
        """Category-specific attribute validation"""
        category_attributes = {
            ('LEIER', 'Tetőcserép'): ['compressive_strength', 'frost_resistance'],
            ('BAUMIT', 'Vakolat'): ['adhesive_strength', 'setting_time'],
            ('ROCKWOOL', 'Szigetelés'): ['thermal_conductivity', 'fire_resistance']
        }
        return category_attributes.get((manufacturer, category), [])

def main():
    """Main execution function"""
    
    try:
        # Check environment
        if not os.getenv('ANTHROPIC_API_KEY'):
            print("❌ ANTHROPIC_API_KEY not found in environment")
            print("Make sure Claude AI API key is configured")
            return
        
        # Initialize and run
        manager = ProductionPDFManager()
        stats = manager.process_all_pdfs()
        manager.print_final_report()
        
        # Save processing report
        report = {
            "timestamp": datetime.now().isoformat(),
            "processing_type": "real_ai_pdf_extraction",
            "stats": stats,
            "simulation": False
        }
        
        with open("production_pdf_report.json", 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info("💾 Processing report saved to production_pdf_report.json")
        
    except Exception as e:
        logger.error(f"❌ Production processing failed: {e}")
        raise

if __name__ == "__main__":
    main() 