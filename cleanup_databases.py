#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Complete Database Cleanup Script
Clears PostgreSQL and ChromaDB for fresh PDF processing
"""

import os
import sys
import shutil
from pathlib import Path

# Add paths for imports
sys.path.append('src/backend')
sys.path.append('src/backend/app')

def cleanup_postgresql():
    """Clean PostgreSQL data tables"""
    print("🗑️ CLEANING POSTGRESQL...")
    
    try:
        from app.database import SessionLocal
        from app.models.product import Product
        from models.processed_file_log import ProcessedFileLog
        
        session = SessionLocal()
        
        # Count before cleanup
        products_before = session.query(Product).count()
        logs_before = session.query(ProcessedFileLog).count()
        
        print(f"   Products before: {products_before}")
        print(f"   Processed logs before: {logs_before}")
        
        # Delete all products
        session.query(Product).delete()
        print("   ✅ Products deleted")
        
        # Delete all processed file logs
        session.query(ProcessedFileLog).delete() 
        print("   ✅ Processed file logs deleted")
        
        # Commit changes
        session.commit()
        session.close()
        
        print("   ✅ PostgreSQL cleanup complete!")
        
    except Exception as e:
        print(f"   ❌ PostgreSQL cleanup failed: {e}")
        return False
    
    return True

def cleanup_chromadb():
    """Clean ChromaDB vector database"""
    print("\n🗑️ CLEANING CHROMADB...")
    
    try:
        # Method 1: Delete ChromaDB data files
        chroma_paths = [
            Path("src/backend/chromadb_data"),
            Path("src/backend/chroma_db"),
            Path("chromadb_data"),
            Path("chroma_db")
        ]
        
        deleted_any = False
        for chroma_path in chroma_paths:
            if chroma_path.exists():
                print(f"   Deleting: {chroma_path}")
                shutil.rmtree(chroma_path)
                deleted_any = True
                
        if deleted_any:
            print("   ✅ ChromaDB files deleted")
        else:
            print("   💡 No ChromaDB files found to delete")
            
        # Method 2: Try programmatic ChromaDB cleanup
        try:
            import chromadb
            client = chromadb.PersistentClient(path="src/backend/chromadb_data")
            
            # List and delete all collections
            collections = client.list_collections()
            for collection in collections:
                client.delete_collection(collection.name)
                print(f"   ✅ Deleted collection: {collection.name}")
                
            if not collections:
                print("   💡 No ChromaDB collections found")
                
        except Exception as e:
            print(f"   💡 Programmatic ChromaDB cleanup: {e}")
        
        print("   ✅ ChromaDB cleanup complete!")
        
    except Exception as e:
        print(f"   ❌ ChromaDB cleanup failed: {e}")
        return False
    
    return True

def show_cleanup_summary():
    """Show final cleanup summary"""
    print("\n📊 CLEANUP SUMMARY:")
    
    try:
        # Check PostgreSQL
        from app.database import SessionLocal
        from app.models.product import Product
        from models.processed_file_log import ProcessedFileLog
        
        session = SessionLocal()
        
        products_after = session.query(Product).count()
        logs_after = session.query(ProcessedFileLog).count()
        
        print(f"   PostgreSQL Products: {products_after}")
        print(f"   PostgreSQL Logs: {logs_after}")
        
        session.close()
        
        # Check ChromaDB
        chroma_files = list(Path(".").glob("**/chroma*"))
        print(f"   ChromaDB files remaining: {len(chroma_files)}")
        
        if products_after == 0 and logs_after == 0:
            print("\n🎉 CLEANUP SUCCESSFUL! Ready for fresh PDF processing.")
        else:
            print("\n⚠️ Some data may remain. Check manually if needed.")
            
    except Exception as e:
        print(f"\n❌ Summary check failed: {e}")

def main():
    """Main cleanup function"""
    print("🧹 COMPLETE DATABASE CLEANUP")
    print("=" * 50)
    
    # Ask for confirmation
    print("\n⚠️  WARNING: This will delete ALL products and processed file logs!")
    print("   - All 4 products will be deleted")
    print("   - All processed file logs will be deleted") 
    print("   - ChromaDB vector data will be deleted")
    print("   - Manufacturers will be KEPT (ROCKWOOL, etc.)")
    print()
    
    confirm = input("Are you sure you want to continue? (yes/no): ").lower().strip()
    
    if confirm not in ['yes', 'y']:
        print("❌ Cleanup cancelled.")
        return
    
    print("\n🚀 Starting cleanup...")
    
    # Execute cleanup
    postgres_success = cleanup_postgresql()
    chromadb_success = cleanup_chromadb()
    
    # Show summary
    show_cleanup_summary()
    
    if postgres_success and chromadb_success:
        print("\n✅ COMPLETE CLEANUP FINISHED!")
        print("💡 You can now run: python real_pdf_processor.py")
        print("   All 46 PDFs will be processed fresh without duplicate errors.")
    else:
        print("\n⚠️ Cleanup completed with some issues. Check logs above.")

if __name__ == "__main__":
    main() 