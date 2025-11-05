#!/usr/bin/env python3
import chromadb
import json

def get_all_chromadb_products():
    """Get all products directly from ChromaDB with complete attributes"""
    try:
        # Connect to ChromaDB
        client = chromadb.HttpClient(host='chroma', port=8000)
        collection = client.get_collection('rockwool_products')
        
        # Get ALL products with metadata and documents
        results = collection.get(include=['metadatas', 'documents'])
        
        print('🏢 ALL ROCKWOOL PRODUCTS FROM CHROMADB')
        print('=' * 80)
        print(f'📊 Total Products in ChromaDB: {len(results["ids"])}')
        print('=' * 80)
        
        # Display every single product with all attributes
        for i, (product_id, metadata, document) in enumerate(zip(results['ids'], results['metadatas'], results['documents']), 1):
            print(f'\n📦 PRODUCT #{i}')
            print('=' * 50)
            print(f'🆔 ChromaDB ID: {product_id}')
            
            # Show ALL metadata attributes
            print('\n📋 ALL CHROMADB METADATA ATTRIBUTES:')
            print('-' * 40)
            for key, value in metadata.items():
                print(f'   {key}: {value}')
            
            # Show document content
            print('\n📄 FULL DOCUMENT CONTENT:')
            print('-' * 40)
            print(document)
            print('=' * 50)
            
            # Add separator for readability
            if i % 5 == 0:
                input(f"\n[Showing {i}/{len(results['ids'])} products. Press Enter to continue...]")
        
        print(f'\n🎯 COMPLETE LIST: {len(results["ids"])} products from ChromaDB displayed')
        
        # Summary of all unique metadata keys
        all_keys = set()
        for metadata in results['metadatas']:
            all_keys.update(metadata.keys())
        
        print(f'\n🔑 ALL METADATA ATTRIBUTES FOUND IN CHROMADB:')
        print('-' * 50)
        for key in sorted(all_keys):
            print(f'   {key}')
        
    except Exception as e:
        print(f'❌ ChromaDB Error: {e}')

if __name__ == "__main__":
    get_all_chromadb_products() 