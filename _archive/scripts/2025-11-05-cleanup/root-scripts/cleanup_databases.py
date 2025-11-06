#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Complete Database Cleanup Script
Clears PostgreSQL and ChromaDB for fresh PDF processing
"""

import sys
from pathlib import Path
import chromadb
from sqlalchemy.orm import Session

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from src.backend.app.database import SessionLocal
    from src.backend.app.models.product import Product
    from src.backend.app.models.manufacturer import Manufacturer
    from src.backend.app.models.category import Category
    from src.backend.models.processed_file_log import ProcessedFileLog
    print("✅ Successfully imported database modules for cleanup.")
except ImportError as e:
    print(f"❌ Failed to import database modules: {e}")
    sys.exit(1)


def clear_postgresql_tables(db: Session):
    """Deletes all data from the relevant tables."""
    try:
        print("\n--- Clearing PostgreSQL Tables ---")
        
        # Order of deletion is important due to foreign key constraints
        num_products = db.query(Product).delete(synchronize_session=False)
        print(f"  - Deleted {num_products} products.")
        
        num_logs = db.query(ProcessedFileLog).delete(synchronize_session=False)
        print(f"  - Deleted {num_logs} processed file logs.")
        
        num_categories = db.query(Category).delete(synchronize_session=False)
        print(f"  - Deleted {num_categories} categories.")
        
        num_manufacturers = db.query(Manufacturer).delete(synchronize_session=False)
        print(f"  - Deleted {num_manufacturers} manufacturers.")
        
        db.commit()
        print("✅ PostgreSQL tables cleared successfully.")
    except Exception as e:
        print(f"❌ Error clearing PostgreSQL tables: {e}")
        db.rollback()


def clear_chromadb_collection(collection_name: str = "pdf_products"):
    """Deletes and recreates a ChromaDB collection."""
    try:
        print(f"\n--- Clearing ChromaDB Collection: {collection_name} ---")
        chroma_client = chromadb.HttpClient(host='localhost', port=8001)
        
        try:
            chroma_client.delete_collection(name=collection_name)
            print(f"  - Collection '{collection_name}' deleted.")
        except ValueError:
            print(f"  - Collection '{collection_name}' did not exist, nothing to delete.")
            
        # Recreate the collection to ensure it's ready for use
        chroma_client.get_or_create_collection(name=collection_name)
        print(f"  - Collection '{collection_name}' created (or already existed).")
        
        print("✅ ChromaDB collection cleared and ready.")
    except Exception as e:
        print(f"❌ Error clearing ChromaDB: {e}")


def main():
    print("🚀 Starting database cleanup process...")
    
    db_session = SessionLocal()
    try:
        clear_postgresql_tables(db_session)
        clear_chromadb_collection()
        print("\n🎉 Database cleanup complete. Ready for a fresh start.")
    finally:
        db_session.close()


if __name__ == "__main__":
    main() 