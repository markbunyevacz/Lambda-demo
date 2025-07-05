#!/usr/bin/env python3
"""
Simple database test script
"""

from sqlalchemy import create_engine, text

def test_database():
    """Test SQLite database"""
    print("🗄️ TESTING DATABASE CONNECTIVITY")
    print("=" * 40)
    
    try:
        engine = create_engine('sqlite:///test.db')
        
        with engine.connect() as conn:
            # Check tables
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]
            print(f"✅ SQLite tables: {tables}")
            
            # Check products if exists
            if 'products' in tables:
                result = conn.execute(text('SELECT COUNT(*) FROM products'))
                count = result.scalar()
                print(f"✅ Products in database: {count}")
            else:
                print("⚠️ No products table found")
                
            # Check processed files if exists
            if 'processed_file_logs' in tables:
                result = conn.execute(text('SELECT COUNT(*) FROM processed_file_logs'))
                count = result.scalar()
                print(f"✅ Processed files logged: {count}")
            else:
                print("⚠️ No processed_file_logs table found")
                
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    test_database() 