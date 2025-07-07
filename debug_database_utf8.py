#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Debug script to find the exact position 66 UTF-8 error in database operations.
"""

import os
import hashlib
from pathlib import Path
import sys

# Add the backend app to path
sys.path.append('src/backend')
sys.path.append('src/backend/app')

def test_database_string_operations():
    """Test all the string operations that happen during database saves"""
    
    print("=== DEBUGGING DATABASE UTF-8 POSITION 66 ERROR ===\n")
    
    # Test data (same as the failing PDF)
    filename = "A bazaltkő természetes erejével.pdf"
    
    print(f"1. FILENAME ANALYSIS:")
    print(f"   Original: {filename}")
    print(f"   UTF-8 bytes: {filename.encode('utf-8')}")
    print(f"   Length: {len(filename)} chars, {len(filename.encode('utf-8'))} bytes")
    
    # Test file hash
    file_hash = hashlib.sha256(b"dummy_content").hexdigest()
    print(f"\n2. FILE HASH:")
    print(f"   Hash: {file_hash[:16]}...")
    print(f"   Length: {len(file_hash)} chars")
    
    # Test the ultra_safe_string function (copy from real_pdf_processor.py)
    def ultra_safe_string(text: str, max_length: int = 255) -> str:
        """Convert any string to ultra-safe UTF-8 format while preserving Hungarian characters"""
        if not text:
            return ""
        
        try:
            # Handle different input types
            if isinstance(text, bytes):
                # Try multiple encodings for bytes
                for encoding in ['utf-8', 'latin1', 'cp1252', 'latin2']:
                    try:
                        text = text.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    # If all fail, use replacement
                    text = text.decode('utf-8', errors='replace')
            
            # Ensure we have a string
            text = str(text)
            
            # Fix common Hungarian encoding issues
            hungarian_fixes = {
                'xE9': 'é', 'x151': 'ő', 'xF3': 'ó', 'xE1': 'á',
                'xF6': 'ö', 'xFC': 'ü', 'xED': 'í', 'xFA': 'ú', 
                'x171': 'ű', 'x170': 'Ű', 'x150': 'Ő', 'xC9': 'É'
            }
            
            for encoded, decoded in hungarian_fixes.items():
                text = text.replace(encoded, decoded)
            
            # Normalize unicode but preserve accented characters
            import unicodedata
            safe_text = unicodedata.normalize('NFC', text)
            
            # Remove only truly problematic characters, keep Hungarian accents and printable characters
            safe_text = ''.join(
                c for c in safe_text 
                if c.isprintable() or c in 'áéíóöőúüűÁÉÍÓÖŐÚÜŰ'
            )
            
            # Final UTF-8 validation
            safe_text = safe_text.encode('utf-8', errors='replace').decode('utf-8')
            
            # Limit length if specified
            if max_length and len(safe_text) > max_length:
                safe_text = safe_text[:max_length-3] + "..."
                
            return safe_text.strip()
            
        except Exception as e:
            print(f"   ERROR in ultra_safe_string: {e}")
            # Emergency fallback - just return simple string
            fallback = ''.join(c for c in str(text) if c.isalnum() or c.isspace())[:max_length or 255]
            return fallback or "unknown"
    
    print(f"\n3. ULTRA_SAFE_STRING TEST:")
    safe_filename = ultra_safe_string(filename, 255)
    print(f"   Input: {filename}")
    print(f"   Output: {safe_filename}")
    print(f"   UTF-8 bytes: {safe_filename.encode('utf-8')}")
    print(f"   Length: {len(safe_filename)} chars, {len(safe_filename.encode('utf-8'))} bytes")
    
    # Test ProcessedFileLog creation simulation
    print(f"\n4. PROCESSED_FILE_LOG SIMULATION:")
    
    try:
        # Simulate creating ProcessedFileLog
        log_data = {
            'file_hash': str(file_hash),
            'content_hash': str(file_hash), 
            'source_filename': safe_filename
        }
        
        print(f"   file_hash: {log_data['file_hash'][:16]}...")
        print(f"   content_hash: {log_data['content_hash'][:16]}...")
        print(f"   source_filename: {log_data['source_filename']}")
        
        # Test repr simulation
        repr_simulation = f"<ProcessedFileLog(filename='{log_data['source_filename']}', file_hash='{log_data['file_hash'][:10]}...')>"
        print(f"   __repr__ simulation: {repr_simulation}")
        print(f"   __repr__ length: {len(repr_simulation)} chars")
        print(f"   __repr__ UTF-8 bytes: {len(repr_simulation.encode('utf-8'))} bytes")
        
        # Check position 66 in repr
        if len(repr_simulation.encode('utf-8')) > 66:
            byte_66 = repr_simulation.encode('utf-8')[66]
            print(f"   Byte at position 66: 0x{byte_66:02x} ({chr(byte_66) if 32 <= byte_66 <= 126 else 'non-ascii'})")
            if byte_66 == 0xe1:
                print(f"   🚨 FOUND THE PROBLEM! Byte 0xe1 at position 66 in __repr__")
            
    except Exception as e:
        print(f"   ERROR in ProcessedFileLog simulation: {e}")
    
    # Test database URL
    print(f"\n5. DATABASE URL TEST:")
    try:
        from database import get_database_url
        db_url = get_database_url()
        print(f"   Database URL: {db_url}")
        print(f"   Length: {len(db_url)} chars")
        if len(db_url) > 66:
            char_66 = db_url[66] if len(db_url) > 66 else 'N/A'
            print(f"   Character at position 66: {repr(char_66)}")
        else:
            print(f"   URL too short for position 66")
    except Exception as e:
        print(f"   ERROR accessing database URL: {e}")
    
    # Test SQLAlchemy import and basic operations
    print(f"\n6. SQLALCHEMY TEST:")
    try:
        from database import SessionLocal
        print(f"   ✅ Database imports successful")
        
        # Try to create a session
        session = SessionLocal()
        print(f"   ✅ Session creation successful")
        session.close()
        
    except Exception as e:
        error_bytes = str(e).encode('utf-8', errors='replace')
        print(f"   ERROR in SQLAlchemy: {str(e)}")
        print(f"   Error UTF-8 bytes: {error_bytes}")
        if len(error_bytes) > 66:
            byte_66 = error_bytes[66]
            print(f"   Error byte at position 66: 0x{byte_66:02x}")
            if byte_66 == 0xe1:
                print(f"   🚨 FOUND THE PROBLEM! Byte 0xe1 at position 66 in SQLAlchemy error")

if __name__ == "__main__":
    test_database_string_operations() 