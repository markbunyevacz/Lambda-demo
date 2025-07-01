#!/usr/bin/env python3
import chromadb
import json

def show_all_products():
    """Display all ROCKWOOL products from ChromaDB with complete metadata"""
    try:
        # Connect to ChromaDB
        client = chromadb.HttpClient(host='chroma', port=8000)
        collection = client.get_collection('rockwool_products')
        
        # Get all products with metadata
        results = collection.get(include=['metadatas', 'documents'])
        
        print('🏢 ROCKWOOL PRODUCTS DATABASE - COMPLETE INVENTORY')
        print('=' * 80)
        print(f'📊 Total Products: {len(results["ids"])}')
        print('=' * 80)
        
        for i, (product_id, metadata, document) in enumerate(zip(results['ids'], results['metadatas'], results['documents']), 1):
            print(f'\n📦 Product #{i}: {metadata.get("name", "Unknown")}')
            print(f'🆔 ID: {product_id} (DB ID: {metadata.get("product_id", "N/A")})')
            print(f'🏭 Manufacturer: {metadata.get("manufacturer", "N/A")}')
            print(f'📂 Category: {metadata.get("category", "N/A")}')
            print(f'🔧 Product Type: {metadata.get("product_type", "N/A")}')
            print(f'🌡️  Thermal Conductivity: {metadata.get("thermal_conductivity", "N/A")}')
            print(f'🔥 Fire Classification: {metadata.get("fire_classification", "N/A")}')
            print(f'📏 Density: {metadata.get("density", "N/A")}')
            print(f'🧱 Material: {metadata.get("material", "N/A")}')
            print(f'✅ Active: {metadata.get("is_active", "N/A")}')
            print(f'📅 Extraction Date: {metadata.get("extraction_date", "N/A")}')
            
            # Check for price information in metadata
            price_found = False
            price_fields = []
            for key, value in metadata.items():
                if any(price_word in key.lower() for price_word in ['price', 'cost', 'ár', 'költség']):
                    price_fields.append(f'{key}: {value}')
                    price_found = True
            
            if price_found:
                print('💰 Price Information:')
                for price_field in price_fields:
                    print(f'   {price_field}')
            else:
                print('💰 Price: Not available in current metadata')
            
            # Show all metadata fields
            print('📋 All Metadata Fields:')
            for key, value in metadata.items():
                if key not in ['name', 'manufacturer', 'category', 'product_type', 
                              'thermal_conductivity', 'fire_classification', 'density', 
                              'material', 'is_active', 'extraction_date', 'product_id']:
                    print(f'   {key}: {value}')
            
            print(f'📄 Document Preview: {document[:300]}...')
            print('-' * 60)
            
            if i >= 5:  # Show first 5 products in detail, then summary
                break
        
        # Show summary of remaining products
        if len(results["ids"]) > 5:
            print(f'\n📈 SUMMARY OF REMAINING {len(results["ids"]) - 5} PRODUCTS:')
            print('=' * 50)
            
            categories = {}
            manufacturers = {}
            
            for metadata in results['metadatas'][5:]:
                cat = metadata.get('category', 'Unknown')
                man = metadata.get('manufacturer', 'Unknown')
                categories[cat] = categories.get(cat, 0) + 1
                manufacturers[man] = manufacturers.get(man, 0) + 1
            
            print('📂 Categories:')
            for cat, count in categories.items():
                print(f'   {cat}: {count} products')
            
            print('\n🏭 Manufacturers:')
            for man, count in manufacturers.items():
                print(f'   {man}: {count} products')
        
        print(f'\n🎯 TOTAL: {len(results["ids"])} ROCKWOOL products in ChromaDB')
        
    except Exception as e:
        print(f'❌ Error connecting to ChromaDB: {e}')

if __name__ == "__main__":
    show_all_products() 