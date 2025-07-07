#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Live debugging script to reproduce the exact database UTF-8 error.
"""

import os
import sys
import hashlib
from pathlib import Path

# Add the backend app to path
sys.path.append('src/backend')
sys.path.append('src/backend/app')

def safe_str_representation(obj, name="object"):
    """Safely get string representation of any object"""
    try:
        str_repr = str(obj)
        print(f"   ✅ {name} string representation successful")
        print(f"      Length: {len(str_repr)} chars")
        if len(str_repr) > 66:
            char_66 = str_repr[66]
            byte_66 = str_repr.encode('utf-8')[66] if len(str_repr.encode('utf-8')) > 66 else None
            print(f"      Character at 66: {repr(char_66)}")
            if byte_66:
                print(f"      Byte at 66: 0x{byte_66:02x}")
                if byte_66 == 0xe1:
                    print(f"      🚨 FOUND PROBLEM! Byte 0xe1 at position 66 in {name}")
        return str_repr
    except Exception as e:
        print(f"   ❌ {name} string representation failed: {e}")
        # Try to analyze the error
        error_str = str(e)
        if "position 66" in error_str and "0xe1" in error_str:
            print(f"      🚨 THIS IS THE PROBLEM! Position 66 error in {name} str() conversion")
        return None

def debug_live_database_operations():
    """Debug live database operations step by step"""
    
    print("=== LIVE DATABASE OPERATIONS DEBUG ===\n")
    
    try:
        # Import database components
        print("1. IMPORTING DATABASE MODULES...")
        from database import SessionLocal
        from models.processed_file_log import ProcessedFileLog
        from models.manufacturer import Manufacturer
        from models.category import Category
        from models.product import Product
        print("   ✅ All database modules imported successfully")
        
        # Create session
        print("\n2. CREATING DATABASE SESSION...")
        session = SessionLocal()
        print("   ✅ Database session created successfully")
        
        # Test data
        filename = "A bazaltkő természetes erejével.pdf"
        file_hash = hashlib.sha256(b"dummy_content_for_testing").hexdigest()
        
        print(f"\n3. TEST DATA PREPARATION...")
        print(f"   Filename: {filename}")
        print(f"   File hash: {file_hash[:16]}...")
        
        # Ultra safe string conversion
        def ultra_safe_string(text: str, max_length: int = 255) -> str:
            if not text:
                return ""
            
            try:
                text = str(text)
                # Hungarian fixes
                hungarian_fixes = {
                    'xE9': 'é', 'x151': 'ő', 'xF3': 'ó', 'xE1': 'á',
                    'xF6': 'ö', 'xFC': 'ü', 'xED': 'í', 'xFA': 'ú', 
                    'x171': 'ű', 'x170': 'Ű', 'x150': 'Ő', 'xC9': 'É'
                }
                
                for encoded, decoded in hungarian_fixes.items():
                    text = text.replace(encoded, decoded)
                
                import unicodedata
                safe_text = unicodedata.normalize('NFC', text)
                safe_text = ''.join(
                    c for c in safe_text 
                    if c.isprintable() or c in 'áéíóöőúüűÁÉÍÓÖŐÚÜŰ'
                )
                safe_text = safe_text.encode('utf-8', errors='replace').decode('utf-8')
                
                if max_length and len(safe_text) > max_length:
                    safe_text = safe_text[:max_length-3] + "..."
                    
                return safe_text.strip()
                
            except Exception as e:
                print(f"      ERROR in ultra_safe_string: {e}")
                fallback = ''.join(c for c in str(text) if c.isalnum() or c.isspace())[:max_length or 255]
                return fallback or "unknown"
        
        safe_filename = ultra_safe_string(filename, 255)
        print(f"   Safe filename: {safe_filename}")
        
        # Step 1: Try ProcessedFileLog creation
        print(f"\n4. CREATING PROCESSED_FILE_LOG...")
        
        try:
            # Create the object
            log_entry = ProcessedFileLog(
                file_hash=str(file_hash),
                content_hash=str(file_hash),
                source_filename=safe_filename,
            )
            print("   ✅ ProcessedFileLog object created successfully")
            
            # Test string representation
            safe_str_representation(log_entry, "ProcessedFileLog")
            
            # Try to add to session
            print("   📋 Adding to session...")
            session.add(log_entry)
            print("   ✅ Added to session successfully")
            
            # Try to commit
            print("   💾 Attempting commit...")
            session.commit()
            print("   ✅ ProcessedFileLog committed successfully!")
            
        except Exception as e:
            print(f"   ❌ ProcessedFileLog failed: {e}")
            # Check if this is the position 66 error
            error_str = str(e)
            if "position 66" in error_str and "0xe1" in error_str:
                print(f"      🚨 THIS IS THE POSITION 66 ERROR SOURCE!")
                
                # Analyze the error in detail
                print(f"      Error string: {repr(error_str)}")
                if len(error_str.encode('utf-8', errors='replace')) > 66:
                    error_bytes = error_str.encode('utf-8', errors='replace')
                    byte_66 = error_bytes[66]
                    print(f"      Error string byte at 66: 0x{byte_66:02x}")
            
            session.rollback()
        
        # Step 2: Try Product creation (if ProcessedFileLog succeeded)
        print(f"\n5. TESTING PRODUCT CREATION...")
        
        try:
            # Get or create manufacturer
            manufacturer = session.query(Manufacturer).filter_by(name="ROCKWOOL").first()
            if not manufacturer:
                print("   📋 Creating ROCKWOOL manufacturer...")
                manufacturer = Manufacturer(
                    name="ROCKWOOL",
                    description="ROCKWOOL insulation products"
                )
                session.add(manufacturer)
                session.flush()
                print("   ✅ ROCKWOOL manufacturer created")
            else:
                print("   ✅ ROCKWOOL manufacturer found")
            
            # Get or create category
            category = session.query(Category).filter_by(name="Building Materials").first()
            if not category:
                print("   📋 Creating Building Materials category...")
                category = Category(name="Building Materials")
                session.add(category)
                session.flush()
                print("   ✅ Building Materials category created")
            else:
                print("   ✅ Building Materials category found")
            
            # Create product with safe data
            print("   📋 Creating Product...")
            safe_name = ultra_safe_string("Test Product from " + filename, 255)
            safe_description = ultra_safe_string(f"Extracted from {filename}", 500)
            safe_text_content = ultra_safe_string("This is test content extracted from the PDF file.", None)
            
            print(f"      Safe name: {safe_name}")
            print(f"      Safe description: {safe_description}")
            print(f"      Safe text content length: {len(safe_text_content)} chars")
            
            product = Product(
                name=safe_name,
                description=safe_description,
                manufacturer_id=manufacturer.id,
                category_id=category.id,
                technical_specs={},
                sku=f"ROCK-TEST-{hash(filename) % 100000}",
                price=None,
                full_text_content=safe_text_content
            )
            
            print("   ✅ Product object created successfully")
            
            # Test string representation
            safe_str_representation(product, "Product")
            
            # Try to add to session
            print("   📋 Adding Product to session...")
            session.add(product)
            print("   ✅ Product added to session successfully")
            
            # Try to commit
            print("   💾 Attempting Product commit...")
            session.commit()
            print("   ✅ Product committed successfully!")
            
        except Exception as e:
            print(f"   ❌ Product creation failed: {e}")
            # Check if this is the position 66 error
            error_str = str(e)
            if "position 66" in error_str and "0xe1" in error_str:
                print(f"      🚨 THIS IS THE POSITION 66 ERROR SOURCE!")
                print(f"      Error string: {repr(error_str)}")
            
            session.rollback()
        
        print(f"\n✅ LIVE DATABASE DEBUG COMPLETE")
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        error_str = str(e)
        if "position 66" in error_str and "0xe1" in error_str:
            print(f"🚨 POSITION 66 ERROR AT TOP LEVEL!")
    
    finally:
        try:
            if 'session' in locals():
                session.close()
                print(f"🔒 Database session closed")
        except:
            pass

if __name__ == "__main__":
    debug_live_database_operations() 