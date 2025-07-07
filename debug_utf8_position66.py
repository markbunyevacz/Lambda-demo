#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Debug script to find the position 66 UTF-8 error"""

filename = "A bazaltkő természetes erejével.pdf"

print("=== FILENAME ANALYSIS ===")
print(f"Filename: {filename}")
print(f"String length: {len(filename)} characters")
print(f"UTF-8 bytes: {filename.encode('utf-8')}")
print(f"UTF-8 bytes length: {len(filename.encode('utf-8'))} bytes")

print("\n=== SIMULATE ProcessedFileLog.__repr__ ===")
file_hash = "abcd1234567890"
repr_string = f"<ProcessedFileLog(filename='{filename}', file_hash='{file_hash[:10]}...')>"

print(f"Repr string: {repr_string}")
print(f"Repr string length: {len(repr_string)} characters")
print(f"Repr UTF-8 bytes length: {len(repr_string.encode('utf-8'))} bytes")

print("\n=== CHARACTER-BY-CHARACTER ANALYSIS ===")
print("Characters around position 60-75:")
for i in range(60, min(len(repr_string), 80)):
    char = repr_string[i] if i < len(repr_string) else "END"
    print(f"Position {i:2d}: {repr(char)}")

print("\n=== UTF-8 BYTE-BY-BYTE ANALYSIS ===")
utf8_bytes = repr_string.encode('utf-8')
print("UTF-8 bytes around position 60-75:")
for i in range(60, min(len(utf8_bytes), 80)):
    byte_val = utf8_bytes[i] if i < len(utf8_bytes) else None
    if byte_val is not None:
        print(f"Byte {i:2d}: 0x{byte_val:02x} ({chr(byte_val) if 32 <= byte_val <= 126 else 'non-ascii'})")

print("\n=== FIND POSITION 66 ===")
if len(utf8_bytes) > 66:
    problem_byte = utf8_bytes[66]
    print(f"Byte at position 66: 0x{problem_byte:02x}")
    if problem_byte == 0xe1:
        print("🚨 FOUND IT! Byte 0xe1 at position 66!")
        print("This is part of a UTF-8 multi-byte sequence")
        # Check surrounding bytes
        context = utf8_bytes[64:69]
        print(f"Context bytes (64-68): {[hex(b) for b in context]}")
    else:
        print(f"Byte at position 66 is 0x{problem_byte:02x}, not 0xe1")
else:
    print("String is too short to have position 66") 