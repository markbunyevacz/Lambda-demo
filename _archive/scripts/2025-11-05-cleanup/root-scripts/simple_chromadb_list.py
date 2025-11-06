#!/usr/bin/env python3
import chromadb

# Connect to ChromaDB
client = chromadb.HttpClient(host='chroma', port=8000)
collection = client.get_collection('rockwool_products')

# Get ALL products with metadata and documents
results = collection.get(include=['metadatas', 'documents'])

print('ALL ROCKWOOL PRODUCTS FROM CHROMADB')
print('=' * 80)
print('Total Products:', len(results["ids"]))
print('=' * 80)

# Display ALL products with complete attributes
for i, (product_id, metadata, document) in enumerate(zip(results['ids'], results['metadatas'], results['documents']), 1):
    print()
    print(f'PRODUCT #{i}')
    print('=' * 50)
    print(f'ChromaDB ID: {product_id}')
    
    print('\nALL METADATA ATTRIBUTES:')
    print('-' * 30)
    for key, value in metadata.items():
        print(f'  {key}: {value}')
    
    print('\nFULL DOCUMENT CONTENT:')
    print('-' * 30)
    print(document)
    print('=' * 50)

print(f'\nTOTAL PRODUCTS IN CHROMADB: {len(results["ids"])}')

# Show all unique metadata keys
all_keys = set()
for metadata in results['metadatas']:
    all_keys.update(metadata.keys())

print('\nALL METADATA KEYS FOUND:')
print('-' * 30)
for key in sorted(all_keys):
    print(f'  {key}') 