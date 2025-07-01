#!/usr/bin/env python3
"""
List All Products from ChromaDB
Comprehensive listing of all ROCKWOOL products in the vector database
"""

import chromadb
from datetime import datetime
import json


def get_chroma_client():
    """Get ChromaDB client with fallback connection logic"""
    # Try localhost first (when running outside Docker)
    try:
        print("🔍 Connecting to ChromaDB (localhost:8001)...")
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


def list_all_products():
    """List all products from ChromaDB with full details"""
    try:
        # Connect to ChromaDB
        client = get_chroma_client()
        
        # Get rockwool_products collection
        collection = client.get_collection("rockwool_products")
        total_count = collection.count()
        
        print(f"\n📚 ROCKWOOL Products Collection")
        print(f"📊 Total Products: {total_count}")
        print("=" * 80)
        
        if total_count == 0:
            print("⚠️  No products found in ChromaDB")
            return
        
        # Get all documents (ChromaDB limits to 100 by default, so we need to handle pagination)
        all_results = collection.get(
            limit=total_count,  # Get all documents
            include=['documents', 'metadatas', 'ids']
        )
        
        documents = all_results.get('documents', [])
        metadatas = all_results.get('metadatas', [])
        ids = all_results.get('ids', [])
        
        print(f"\n🔍 Listing {len(documents)} Products:\n")
        
        # Sort by product name for better readability
        product_data = list(zip(ids, documents, metadatas))
        product_data.sort(key=lambda x: x[2].get('name', '').lower())
        
        for i, (doc_id, document, metadata) in enumerate(product_data, 1):
            # Extract metadata
            name = metadata.get('name', 'Unknown Product')
            product_type = metadata.get('product_type', 'N/A')
            category = metadata.get('category', 'Uncategorized')
            thermal_conductivity = metadata.get('thermal_conductivity', 'N/A')
            source_file = metadata.get('source_file', 'N/A')
            page_count = metadata.get('page_count', 'N/A')
            
            print(f"📦 {i:2d}. {name}")
            print(f"    🏷️  Type: {product_type}")
            print(f"    📂 Category: {category}")
            print(f"    🌡️  Thermal λ: {thermal_conductivity} W/mK")
            print(f"    📄 Source: {source_file}")
            print(f"    📊 Pages: {page_count}")
            print(f"    🆔 ID: {doc_id}")
            
            # Show document preview (first 150 characters)
            if document:
                preview = document[:150].replace('\n', ' ').strip()
                print(f"    📝 Content: {preview}...")
            
            print()
        
        # Statistics
        print("=" * 80)
        print("📈 COLLECTION STATISTICS:")
        
        # Count by category
        categories = {}
        product_types = {}
        thermal_values = []
        
        for metadata in metadatas:
            # Category stats
            cat = metadata.get('category', 'Uncategorized')
            categories[cat] = categories.get(cat, 0) + 1
            
            # Product type stats
            ptype = metadata.get('product_type', 'Unknown')
            product_types[ptype] = product_types.get(ptype, 0) + 1
            
            # Thermal conductivity stats
            thermal = metadata.get('thermal_conductivity', '')
            if thermal and thermal != 'N/A':
                try:
                    thermal_val = float(thermal.replace(' W/mK', '').replace(',', '.'))
                    thermal_values.append(thermal_val)
                except:
                    pass
        
        print(f"\n🏷️  Categories ({len(categories)}):")
        for cat, count in sorted(categories.items()):
            print(f"   • {cat}: {count} products")
        
        print(f"\n📦 Product Types ({len(product_types)}):")
        for ptype, count in sorted(product_types.items()):
            print(f"   • {ptype}: {count} products")
        
        if thermal_values:
            print(f"\n🌡️  Thermal Conductivity Range:")
            print(f"   • Min: {min(thermal_values):.3f} W/mK")
            print(f"   • Max: {max(thermal_values):.3f} W/mK")
            print(f"   • Avg: {sum(thermal_values)/len(thermal_values):.3f} W/mK")
            print(f"   • Values available: {len(thermal_values)}/{total_count}")
        
        print(f"\n✅ Successfully listed all {total_count} products from ChromaDB!")
        
    except Exception as e:
        print(f"❌ Error listing products: {e}")
        print("💡 Make sure ChromaDB is running: docker-compose up -d chroma")


def export_products_json():
    """Export all products to JSON file for analysis"""
    try:
        client = get_chroma_client()
        collection = client.get_collection("rockwool_products")
        
        all_results = collection.get(
            limit=collection.count(),
            include=['documents', 'metadatas', 'ids']
        )
        
        # Create structured export
        export_data = {
            "collection_name": "rockwool_products",
            "total_count": collection.count(),
            "exported_at": datetime.now().isoformat(),
            "products": []
        }
        
        for doc_id, document, metadata in zip(
            all_results['ids'], 
            all_results['documents'], 
            all_results['metadatas']
        ):
            export_data["products"].append({
                "id": doc_id,
                "metadata": metadata,
                "content_preview": document[:200] if document else None,
                "content_length": len(document) if document else 0
            })
        
        # Save to JSON file
        with open('chroma_products_export.json', 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Exported {len(export_data['products'])} products to 'chroma_products_export.json'")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")


if __name__ == "__main__":
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"🕐 ChromaDB Product Listing - {timestamp}")
    print("=" * 80)
    
    list_all_products()
    
    # Ask if user wants JSON export
    print("\n" + "=" * 80)
    print("💾 Export Options:")
    print("To export all products to JSON, run:")
    print("python list_all_chroma_products.py --export")
    
    import sys
    if '--export' in sys.argv:
        print("\n📤 Exporting to JSON...")
        export_products_json() 