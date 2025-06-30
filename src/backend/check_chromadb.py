#!/usr/bin/env python3
"""
ChromaDB Status Checker
Connects to ChromaDB and displays collection information
"""

import chromadb
from datetime import datetime


def get_chroma_client():
    """Get ChromaDB client with fallback connection logic"""
    # Try localhost first (when running outside Docker)
    try:
        print("🔍 Trying localhost connection (localhost:8001)...")
        client = chromadb.HttpClient(host="localhost", port=8001)
        client.heartbeat()  # Test connection
        print("✅ Connected via localhost")
        return client
    except Exception:
        # Fallback to Docker internal network (when running inside Docker)
        try:
            print("🔍 Trying Docker network connection (chroma:8000)...")
            client = chromadb.HttpClient(host="chroma", port=8000)
            client.heartbeat()  # Test connection
            print("✅ Connected via Docker network")
            return client
        except Exception as e:
            raise Exception(f"Cannot connect to ChromaDB: {e}")


def check_chromadb_status():
    try:
        # Connect to ChromaDB
        client = get_chroma_client()
        
        # Test connection
        heartbeat = client.heartbeat()
        print(f"✅ ChromaDB is running! Heartbeat: {heartbeat}")
        
        # List all collections
        collections = client.list_collections()
        print(f"\n📚 Collections found: {len(collections)}")
        
        for collection in collections:
            print(f"  - {collection.name}")
            
            # Get collection details
            count = collection.count()
            print(f"    📊 Documents: {count}")
            
            # If this is our Rockwool collection, show sample data
            if collection.name == "rockwool_products":
                print("    🔍 Querying sample products...")
                
                # Get first 3 documents
                results = collection.get(limit=3)
                
                if results['documents']:
                    print("    📄 Sample products:")
                    docs = results['documents'] or []
                    metas = results['metadatas'] or []
                    for i, (doc, metadata) in enumerate(zip(docs, metas)):
                        name = metadata.get('name', 'Unknown')
                        ptype = metadata.get('product_type', 'Unknown type')
                        thermal = metadata.get('thermal_conductivity', 'N/A')
                        print(f"      {i+1}. {name} ({ptype})")
                        print(f"         λ: {thermal} W/mK")
                        print(f"         Text preview: {doc[:100]}...")
                        print()
                else:
                    print("    ⚠️  Collection exists but no documents found")
        
        if not collections:
            print("⚠️  No collections found. RAG pipeline may not be "
                  "initialized yet.")
            
    except Exception as e:
        print(f"❌ Error connecting to ChromaDB: {e}")
        print("💡 Make sure ChromaDB is running: docker-compose up -d")


if __name__ == "__main__":
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"🕐 ChromaDB Status Check - {timestamp}")
    print("=" * 60)
    check_chromadb_status() 