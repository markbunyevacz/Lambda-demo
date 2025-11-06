#!/usr/bin/env python3
"""
Database Duplicate Cleanup Script
=================================

Removes duplicate products from the database, keeping the most recent version.
"""

import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "src" / "backend"))

from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database import get_db
from app.models.product import Product
from app.models.manufacturer import Manufacturer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DuplicateCleanupManager:
    """Manages cleanup of duplicate products"""
    
    def __init__(self):
        self.db = next(get_db())
        self.stats = {
            'total_products': 0,
            'duplicates_found': 0,
            'duplicates_removed': 0,
            'unique_remaining': 0
        }
    
    def analyze_duplicates(self):
        """Analyze current duplicate situation"""
        print("🔍 ANALYZING DATABASE DUPLICATES")
        print("=" * 50)
        
        # Get total products
        total = self.db.query(Product).count()
        self.stats['total_products'] = total
        print(f"📊 Total products in database: {total}")
        
        # Find duplicates by name and manufacturer
        duplicates_query = (
            self.db.query(
                Product.name,
                Product.manufacturer_id,
                func.count(Product.id).label('count')
            )
            .group_by(Product.name, Product.manufacturer_id)
            .having(func.count(Product.id) > 1)
        )
        
        duplicate_groups = duplicates_query.all()
        self.stats['duplicates_found'] = len(duplicate_groups)
        
        print(f"🔄 Product names with duplicates: {len(duplicate_groups)}")
        
        # Show top duplicates
        print("\n📋 Top duplicate products:")
        for name, mfr_id, count in sorted(duplicate_groups, key=lambda x: x[2], reverse=True)[:10]:
            manufacturer = self.db.query(Manufacturer).filter(Manufacturer.id == mfr_id).first()
            mfr_name = manufacturer.name if manufacturer else "Unknown"
            print(f"   • {name} ({mfr_name}): {count} copies")
        
        return duplicate_groups
    
    def clean_duplicates(self, duplicate_groups):
        """Remove duplicate products, keeping the most recent"""
        print(f"\n🧹 CLEANING {len(duplicate_groups)} DUPLICATE GROUPS")
        print("=" * 50)
        
        removed_count = 0
        
        for name, manufacturer_id, count in duplicate_groups:
            # Get all products with this name/manufacturer
            products = (
                self.db.query(Product)
                .filter(
                    Product.name == name,
                    Product.manufacturer_id == manufacturer_id
                )
                .order_by(desc(Product.created_at))
                .all()
            )
            
            if len(products) <= 1:
                continue
                
            # Keep the most recent (first in desc order)
            to_keep = products[0]
            to_remove = products[1:]
            
            print(f"📄 {name}")
            print(f"   ✅ Keeping: ID {to_keep.id} (created: {to_keep.created_at})")
            
            for product in to_remove:
                print(f"   ❌ Removing: ID {product.id} (created: {product.created_at})")
                self.db.delete(product)
                removed_count += 1
        
        # Commit all deletions
        self.db.commit()
        self.stats['duplicates_removed'] = removed_count
        
        print(f"\n✅ Removed {removed_count} duplicate products")
        return removed_count
    
    def verify_cleanup(self):
        """Verify cleanup was successful"""
        print("\n🔍 VERIFYING CLEANUP")
        print("=" * 50)
        
        # Count remaining products
        remaining = self.db.query(Product).count()
        self.stats['unique_remaining'] = remaining
        
        # Check for remaining duplicates
        remaining_duplicates = (
            self.db.query(
                Product.name,
                Product.manufacturer_id,
                func.count(Product.id).label('count')
            )
            .group_by(Product.name, Product.manufacturer_id)
            .having(func.count(Product.id) > 1)
            .count()
        )
        
        print(f"📊 Products remaining: {remaining}")
        print(f"🔄 Duplicate groups remaining: {remaining_duplicates}")
        
        if remaining_duplicates == 0:
            print("✅ SUCCESS: All duplicates removed!")
        else:
            print(f"⚠️  WARNING: {remaining_duplicates} duplicate groups still exist")
        
        return remaining_duplicates == 0
    
    def print_summary(self):
        """Print final cleanup summary"""
        print("\n" + "=" * 60)
        print("🏁 DUPLICATE CLEANUP SUMMARY")
        print("=" * 60)
        print(f"📊 Original products: {self.stats['total_products']}")
        print(f"🔄 Duplicate groups found: {self.stats['duplicates_found']}")
        print(f"❌ Duplicates removed: {self.stats['duplicates_removed']}")
        print(f"✅ Unique products remaining: {self.stats['unique_remaining']}")
        
        if self.stats['duplicates_removed'] > 0:
            efficiency = (self.stats['duplicates_removed'] / self.stats['total_products']) * 100
            print(f"📈 Database efficiency improved by: {efficiency:.1f}%")
        
        print("=" * 60)
    
    def run_cleanup(self):
        """Run complete duplicate cleanup process"""
        try:
            # Step 1: Analyze
            duplicate_groups = self.analyze_duplicates()
            
            if not duplicate_groups:
                print("✅ No duplicates found! Database is clean.")
                return True
            
            # Step 2: Clean
            removed = self.clean_duplicates(duplicate_groups)
            
            # Step 3: Verify
            success = self.verify_cleanup()
            
            # Step 4: Summary
            self.print_summary()
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            self.db.rollback()
            return False
        finally:
            self.db.close()

def main():
    """Main cleanup function"""
    print("🚀 LAMBDA.HU DATABASE DUPLICATE CLEANUP")
    print("=" * 60)
    
    cleanup_manager = DuplicateCleanupManager()
    success = cleanup_manager.run_cleanup()
    
    if success:
        print("🎉 Database cleanup completed successfully!")
        return 0
    else:
        print("❌ Database cleanup failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 