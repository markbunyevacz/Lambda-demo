#!/usr/bin/env python3
"""
Clean up test data from PostgreSQL
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def cleanup_test_data():
    """Clean up test data from PostgreSQL"""
    
    print("🧹 CLEANING UP TEST DATA")
    print("=" * 30)
    
    # Load environment
    load_dotenv("../../.env")
    
    # Connect to PostgreSQL
    url = 'postgresql://lambda_user:Cz31n1ng3r@localhost:5432/lambda_db?client_encoding=utf8&application_name=lambda_scraper'
    
    try:
        engine = create_engine(url)
        
        with engine.connect() as conn:
            # Delete test data
            conn.execute(text("DELETE FROM products WHERE sku LIKE 'TEST-%'"))
            conn.execute(text("DELETE FROM categories WHERE name LIKE 'Test%'"))
            conn.execute(text("DELETE FROM manufacturers WHERE name LIKE 'TEST_%'"))
            conn.execute(text("DELETE FROM processed_file_logs WHERE file_hash LIKE 'test_hash_%'"))
            conn.commit()
            
            print("✅ Test data cleaned up successfully")
            return True
            
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False

if __name__ == "__main__":
    cleanup_test_data() 