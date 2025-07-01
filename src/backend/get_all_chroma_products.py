#!/usr/bin/env python3
"""
Get ALL 46 products from ChromaDB - Complete List
"""

import chromadb

def get_chroma_client():
    try:
        client = chromadb.HttpClient(host="chroma", port=8000)
        client.heartbeat()
        return client
    except Exception:
        client = chromadb.HttpClient(host="localhost", port=8001)
        client.heartbeat()
        return client

def get_all_products():
    client = get_chroma_client()
    collection = client.get_collection("rockwool_products")
    
    print(f"📊 Total Documents: {collection.count()}")
    
    # Get ALL 46 documents
    results = collection.get(
        limit=46,  # Get all documents
        include=['documents', 'metadatas', 'ids']
    )
    
    print(f"\n🔍 ALL {len(results['documents'])} PRODUCTS:")
    print("=" * 80)
    
    for i, (doc_id, document, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas']), 1):
        name = metadata.get('name', 'NO NAME')
        source = metadata.get('source_file', 'NO SOURCE')
        category = metadata.get('category', 'NO CATEGORY')
        product_type = metadata.get('product_type', 'NO TYPE')
        
        print(f"{i:2d}. {name}")
        print(f"    📁 {source}")
        print(f"    📂 {category} | {product_type}")
        print(f"    📝 Content length: {len(document) if document else 0} chars")
        if document:
            preview = document[:80].replace('\n', ' ')
            print(f"    💬 '{preview}...'")
        print()

if __name__ == "__main__":
    get_all_products() 