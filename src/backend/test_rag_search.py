#!/usr/bin/env python3
"""
RAG Search Test
Testing semantic search functionality with multilingual queries
"""

import chromadb

def get_chroma_client():
    """Get ChromaDB client with fallback connection logic"""
    # Try localhost first (when running outside Docker)
    try:
        client = chromadb.HttpClient(host="localhost", port=8001)
        client.heartbeat()  # Test connection
        return client
    except Exception:
        # Fallback to Docker internal network (when running inside Docker)
        try:
            client = chromadb.HttpClient(host="chroma", port=8000)
            client.heartbeat()  # Test connection
            return client
        except Exception as e:
            raise Exception(f"Cannot connect to ChromaDB: {e}")

def test_rag_search():
    print("🧪 Testing RAG Semantic Search...")
    
    # Connect to ChromaDB
    client = get_chroma_client()
    collection = client.get_collection("rockwool_products")
    
    print(f"📚 Collection has {collection.count()} documents")
    
    # Test 1: Hungarian search
    print("\n🔍 Test 1: Hungarian Search - 'lapostető hőszigetelés'")
    results1 = collection.query(
        query_texts=["lapostető hőszigetelés"], 
        n_results=3
    )
    
    for i, (doc, meta) in enumerate(zip(results1['documents'][0], results1['metadatas'][0])):
        name = meta.get('name', 'Unknown')
        category = meta.get('category', 'N/A')
        print(f"  {i+1}. {name} ({category})")
    
    # Test 2: English search
    print("\n🔍 Test 2: English Search - 'thermal insulation low conductivity'")
    results2 = collection.query(
        query_texts=["thermal insulation low conductivity"], 
        n_results=3
    )
    
    for i, (doc, meta) in enumerate(zip(results2['documents'][0], results2['metadatas'][0])):
        name = meta.get('name', 'Unknown')
        category = meta.get('category', 'N/A')
        print(f"  {i+1}. {name} ({category})")
    
    # Test 3: Technical search
    print("\n🔍 Test 3: Technical Search - 'fire protection high temperature'")
    results3 = collection.query(
        query_texts=["fire protection high temperature"], 
        n_results=3
    )
    
    for i, (doc, meta) in enumerate(zip(results3['documents'][0], results3['metadatas'][0])):
        name = meta.get('name', 'Unknown')
        category = meta.get('category', 'N/A')
        print(f"  {i+1}. {name} ({category})")
    
    print("\n✅ RAG Semantic Search Test Complete!")

if __name__ == "__main__":
    test_rag_search() 