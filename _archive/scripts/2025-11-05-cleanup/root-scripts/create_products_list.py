#!/usr/bin/env python3
import chromadb
import json
import csv

def create_complete_products_list():
    """Create organized list of all ChromaDB products with attributes"""
    
    # Connect to ChromaDB
    client = chromadb.HttpClient(host='chroma', port=8000)
    collection = client.get_collection('rockwool_products')
    
    # Get ALL products
    results = collection.get(include=['metadatas', 'documents'])
    
    print(f"Creating complete list of {len(results['ids'])} products...")
    
    # Create organized list
    product_list = []
    for i, (product_id, metadata, document) in enumerate(zip(results['ids'], results['metadatas'], results['documents']), 1):
        product_info = {
            'number': i,
            'chromadb_id': product_id,
            'name': metadata.get('name', 'Unknown'),
            'product_id': metadata.get('product_id', 'N/A'),
            'category': metadata.get('category', 'N/A'),
            'manufacturer': metadata.get('manufacturer', 'N/A'),
            'material': metadata.get('material', 'N/A'),
            'product_type': metadata.get('product_type', 'N/A'),
            'thermal_conductivity': metadata.get('thermal_conductivity', 'N/A'),
            'fire_classification': metadata.get('fire_classification', 'N/A'),
            'density': metadata.get('density', 'N/A'),
            'is_active': metadata.get('is_active', 'N/A'),
            'extraction_date': metadata.get('extraction_date', 'N/A'),
            'document': document
        }
        product_list.append(product_info)
    
    # Save as JSON
    with open('/app/chromadb_products_list.json', 'w', encoding='utf-8') as f:
        json.dump(product_list, f, indent=2, ensure_ascii=False)
    
    # Save as CSV for easy viewing
    with open('/app/chromadb_products_list.csv', 'w', newline='', encoding='utf-8') as f:
        if product_list:
            fieldnames = ['number', 'chromadb_id', 'name', 'product_id', 'category', 
                         'manufacturer', 'material', 'product_type', 'thermal_conductivity', 
                         'fire_classification', 'density', 'is_active', 'extraction_date']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for product in product_list:
                row = {k: v for k, v in product.items() if k != 'document'}
                writer.writerow(row)
    
    # Create readable text file
    with open('/app/chromadb_products_list.txt', 'w', encoding='utf-8') as f:
        f.write("COMPLETE ROCKWOOL PRODUCTS LIST FROM CHROMADB\n")
        f.write("=" * 60 + "\n")
        f.write(f"Total Products: {len(product_list)}\n")
        f.write("=" * 60 + "\n\n")
        
        for product in product_list:
            f.write(f"PRODUCT #{product['number']}: {product['name']}\n")
            f.write(f"ChromaDB ID: {product['chromadb_id']}\n")
            f.write(f"Product ID: {product['product_id']}\n")
            f.write(f"Category: {product['category']}\n")
            f.write(f"Manufacturer: {product['manufacturer']}\n")
            f.write(f"Material: {product['material']}\n")
            f.write(f"Product Type: {product['product_type']}\n")
            f.write(f"Thermal Conductivity: {product['thermal_conductivity']}\n")
            f.write(f"Fire Classification: {product['fire_classification']}\n")
            f.write(f"Density: {product['density']}\n")
            f.write(f"Active: {product['is_active']}\n")
            f.write(f"Extraction Date: {product['extraction_date']}\n")
            f.write("-" * 50 + "\n\n")
    
    print(f"✅ Complete product lists created:")
    print(f"   📄 JSON: /app/chromadb_products_list.json")
    print(f"   📊 CSV: /app/chromadb_products_list.csv") 
    print(f"   📋 TXT: /app/chromadb_products_list.txt")
    print(f"📊 Total products: {len(product_list)}")

if __name__ == "__main__":
    create_complete_products_list() 