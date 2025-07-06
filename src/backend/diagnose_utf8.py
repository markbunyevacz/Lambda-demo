#!/usr/bin/env python3
"""
🔍 UTF-8 Adatbázis Diagnosztikai Szkript
"""

import sys
import os
sys.path.append('.')

def test_database_utf8():
    """Test database UTF-8 handling"""
    try:
        from app.database import get_db
        from app.models.manufacturer import Manufacturer
        from app.models.product import Product
        
        print("🔍 UTF-8 Adatbázis Diagnosztika")
        print("=" * 50)
        
        # Get database session
        db = next(get_db())
        print("✅ Database connection successful")
        
        # Test manufacturer count
        mfr_count = db.query(Manufacturer).count()
        print(f"✅ Manufacturers count: {mfr_count}")
        
        # Test product count  
        prod_count = db.query(Product).count()
        print(f"✅ Products count: {prod_count}")
        
        # Test actual data retrieval
        print("\n🧪 Testing data retrieval...")
        manufacturers = db.query(Manufacturer).limit(3).all()
        
        for i, mfr in enumerate(manufacturers, 1):
            try:
                # Try to access name safely
                name_raw = mfr.name
                name_safe = str(name_raw).encode('utf-8', errors='ignore').decode('utf-8')
                print(f"  {i}. Manufacturer: {repr(name_safe)}")
                
                # Test website field
                website_raw = mfr.website
                if website_raw:
                    website_safe = str(website_raw).encode('utf-8', errors='ignore').decode('utf-8')
                    print(f"     Website: {repr(website_safe)}")
                    
            except Exception as e:
                error_msg = str(e).encode('utf-8', errors='ignore').decode('utf-8')
                print(f"  ❌ Error accessing manufacturer {i}: {error_msg}")
        
        db.close()
        print("\n✅ Diagnostic completed successfully")
        return True
        
    except Exception as e:
        error_msg = str(e).encode('utf-8', errors='ignore').decode('utf-8')
        print(f"❌ Database diagnostic failed: {error_msg}")
        
        # Print more detailed error info
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_database_utf8() 