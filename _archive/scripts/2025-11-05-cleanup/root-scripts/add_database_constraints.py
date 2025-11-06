#!/usr/bin/env python3
"""
Database Constraints Setup
==========================

Adds database-level constraints to prevent duplicate products.
"""

import sys
import logging
from pathlib import Path

# Add backend to path  
sys.path.append(str(Path(__file__).parent / "src" / "backend"))

from sqlalchemy import text
from app.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_unique_constraints():
    """Add database constraints to prevent duplicates"""
    print("🔧 ADDING DATABASE CONSTRAINTS")
    print("=" * 50)
    
    constraints = [
        {
            "name": "unique_product_name_manufacturer",
            "table": "products", 
            "sql": """
                ALTER TABLE products 
                ADD CONSTRAINT unique_product_name_manufacturer 
                UNIQUE (name, manufacturer_id)
            """,
            "description": "Prevent duplicate products with same name + manufacturer"
        },
        {
            "name": "unique_product_sku",
            "table": "products",
            "sql": """
                ALTER TABLE products
                ADD CONSTRAINT unique_product_sku_not_null
                UNIQUE (sku)
            """,
            "description": "Ensure SKU uniqueness (already in model, but enforce)"
        }
    ]
    
    success_count = 0
    
    for constraint in constraints:
        try:
            # Check if constraint already exists
            check_sql = f"""
                SELECT COUNT(*) FROM pg_constraint 
                WHERE conname = '{constraint['name']}'
            """
            
            with engine.connect() as conn:
                result = conn.execute(text(check_sql))
                exists = result.scalar() > 0
                
                if exists:
                    print(f"✅ {constraint['name']}: Already exists")
                    success_count += 1
                    continue
                
                # Add constraint
                conn.execute(text(constraint['sql']))
                conn.commit()
                print(f"✅ {constraint['name']}: Added successfully")
                print(f"   📋 {constraint['description']}")
                success_count += 1
                
        except Exception as e:
            if "already exists" in str(e):
                print(f"✅ {constraint['name']}: Already exists")
                success_count += 1
            else:
                print(f"❌ {constraint['name']}: Failed - {e}")
    
    return success_count == len(constraints)

def add_performance_indexes():
    """Add indexes for better duplicate detection performance"""
    print("\n🚀 ADDING PERFORMANCE INDEXES")
    print("=" * 50)
    
    indexes = [
        {
            "name": "idx_products_name_manufacturer",
            "sql": """
                CREATE INDEX IF NOT EXISTS idx_products_name_manufacturer
                ON products (name, manufacturer_id)
            """,
            "description": "Fast duplicate detection by name + manufacturer"
        },
        {
            "name": "idx_products_source_url",
            "sql": """
                CREATE INDEX IF NOT EXISTS idx_products_source_url
                ON products (source_url)
                WHERE source_url IS NOT NULL
            """,
            "description": "Fast duplicate detection by source URL"
        },
        {
            "name": "idx_products_created_at",
            "sql": """
                CREATE INDEX IF NOT EXISTS idx_products_created_at
                ON products (created_at DESC)
            """,
            "description": "Fast sorting for duplicate cleanup"
        }
    ]
    
    success_count = 0
    
    for index in indexes:
        try:
            with engine.connect() as conn:
                conn.execute(text(index['sql']))
                conn.commit()
                print(f"✅ {index['name']}: Created")
                print(f"   📋 {index['description']}")
                success_count += 1
                
        except Exception as e:
            if "already exists" in str(e):
                print(f"✅ {index['name']}: Already exists")
                success_count += 1
            else:
                print(f"❌ {index['name']}: Failed - {e}")
    
    return success_count == len(indexes)

def main():
    """Main function"""
    print("🚀 DATABASE CONSTRAINTS & INDEXES SETUP")
    print("=" * 60)
    
    # Add constraints
    constraints_ok = add_unique_constraints()
    
    # Add indexes  
    indexes_ok = add_performance_indexes()
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 DATABASE SETUP SUMMARY")
    print("=" * 60)
    
    if constraints_ok and indexes_ok:
        print("✅ All constraints and indexes added successfully!")
        print("🛡️  Database is now protected against duplicates")
        return 0
    else:
        print("❌ Some constraints or indexes failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 