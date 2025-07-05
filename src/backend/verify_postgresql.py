#!/usr/bin/env python3
"""
PostgreSQL Production Verification Script
Tests database connectivity, table creation, and data persistence
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add backend to path
sys.path.append('.')

def test_postgresql_connection():
    """Test PostgreSQL connectivity and verify production setup"""
    
    print("🗄️ POSTGRESQL PRODUCTION VERIFICATION")
    print("=" * 60)
    
    # Load environment
    load_dotenv("../../.env")
    
    # Test different connection methods
    connection_methods = [
        {
            'name': 'Docker PostgreSQL (Production)',
            'url': 'postgresql://lambda_user:Cz31n1ng3r@localhost:5432/lambda_db?client_encoding=utf8&application_name=lambda_scraper'
        },
        {
            'name': 'Environment Variable',
            'url': os.getenv('DATABASE_URL')
        }
    ]
    
    successful_connection = None
    
    for method in connection_methods:
        if not method['url']:
            print(f"⚠️ {method['name']}: No URL available")
            continue
            
        print(f"\n🔍 Testing: {method['name']}")
        print(f"   URL: {method['url'][:50]}...")
        
        try:
            # Test basic connection
            engine = create_engine(method['url'])
            
            with engine.connect() as conn:
                # Test basic query
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"   ✅ Connection successful!")
                print(f"   📊 PostgreSQL Version: {version[:50]}...")
                
                # Test table listing
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                print(f"   📋 Tables found: {len(tables)} - {tables}")
                
                # Test UTF-8 handling
                conn.execute(text("SELECT 'áéíóöőúüű' as test_hungarian"))
                print(f"   ✅ UTF-8 encoding working!")
                
                successful_connection = method
                break
                
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            continue
    
    return successful_connection

def test_data_persistence(connection_info):
    """Test actual data persistence in PostgreSQL"""
    
    if not connection_info:
        print("❌ No successful PostgreSQL connection available")
        return False
        
    print(f"\n💾 TESTING DATA PERSISTENCE")
    print("=" * 40)
    
    try:
        engine = create_engine(connection_info['url'])
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Import models
        from app.models.manufacturer import Manufacturer
        from app.models.category import Category
        from app.models.product import Product
        from models.processed_file_log import ProcessedFileLog
        
        # Create tables if they don't exist
        from app.models.manufacturer import Base as ManufacturerBase
        from app.models.category import Base as CategoryBase
        from app.models.product import Base as ProductBase
        from models.processed_file_log import Base as LogBase
        
        print("🏗️ Creating/verifying database tables...")
        ManufacturerBase.metadata.create_all(bind=engine)
        CategoryBase.metadata.create_all(bind=engine)
        ProductBase.metadata.create_all(bind=engine)
        LogBase.metadata.create_all(bind=engine)
        print("   ✅ Tables created/verified")
        
        # Test data insertion
        with SessionLocal() as session:
            # Test manufacturer
            test_manufacturer = Manufacturer(
                name="TEST_ROCKWOOL",
                description="Test manufacturer for verification"
            )
            session.add(test_manufacturer)
            session.commit()
            session.refresh(test_manufacturer)
            print(f"   ✅ Manufacturer created: ID {test_manufacturer.id}")
            
            # Test category
            test_category = Category(
                name="Test Category",
                description="Test category for verification"
            )
            session.add(test_category)
            session.commit()
            session.refresh(test_category)
            print(f"   ✅ Category created: ID {test_category.id}")
            
            # Test product
            test_product = Product(
                name="Test Product - ROCKWOOL Verification",
                description="Test product for PostgreSQL verification",
                manufacturer_id=test_manufacturer.id,
                category_id=test_category.id,
                sku="TEST-ROCK-001",
                technical_specifications={
                    "thermal_conductivity": "0.035 W/mK",
                    "density": "150 kg/m³",
                    "test_field": "verification_data"
                },
                price=99.99
            )
            session.add(test_product)
            session.commit()
            session.refresh(test_product)
            print(f"   ✅ Product created: ID {test_product.id}")
            
            # Test processed file log
            test_log = ProcessedFileLog(
                file_hash="test_hash_" + str(datetime.now().timestamp()),
                content_hash="test_content_hash",
                source_filename="test_verification.pdf"
            )
            session.add(test_log)
            session.commit()
            session.refresh(test_log)
            print(f"   ✅ Processed file log created: ID {test_log.id}")
            
            # Verify data retrieval
            retrieved_product = session.query(Product).filter(
                Product.sku == "TEST-ROCK-001"
            ).first()
            
            if retrieved_product:
                print(f"   ✅ Data retrieval successful:")
                print(f"      Product: {retrieved_product.name}")
                print(f"      Manufacturer: {retrieved_product.manufacturer.name}")
                print(f"      Category: {retrieved_product.category.name}")
                print(f"      Specs: {len(retrieved_product.technical_specifications)} fields")
                
                # Clean up test data
                session.delete(test_log)
                session.delete(retrieved_product)
                session.delete(test_category)
                session.delete(test_manufacturer)
                session.commit()
                print(f"   ✅ Test data cleaned up")
                
                return True
            else:
                print(f"   ❌ Data retrieval failed")
                return False
                
    except Exception as e:
        print(f"❌ Data persistence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main verification function"""
    
    print("🚀 POSTGRESQL PRODUCTION VERIFICATION")
    print("Testing database connectivity and data persistence")
    print()
    
    # Test connection
    connection_info = test_postgresql_connection()
    
    if connection_info:
        print(f"\n✅ PostgreSQL connection successful via: {connection_info['name']}")
        
        # Test data persistence
        persistence_success = test_data_persistence(connection_info)
        
        if persistence_success:
            print(f"\n🎉 POSTGRESQL VERIFICATION COMPLETE!")
            print("   ✅ Database connectivity working")
            print("   ✅ Table creation working")
            print("   ✅ Data insertion working")
            print("   ✅ Data retrieval working")
            print("   ✅ UTF-8 encoding working")
            print("\n🚀 Ready for production PDF processing!")
        else:
            print(f"\n⚠️ PostgreSQL connection works but data persistence failed")
            
    else:
        print(f"\n❌ PostgreSQL connection failed")
        print("   💡 Try starting Docker: docker-compose up -d db")
        print("   💡 Check connection string in app/database.py")

if __name__ == "__main__":
    main() 