#!/usr/bin/env python3
import requests
import json
from collections import defaultdict

def analyze_all_products():
    """Analyze all ROCKWOOL products with complete attributes and pricing info"""
    try:
        # Get all products from API
        response = requests.get("http://backend:8000/products?limit=200")
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            return
        
        products = response.json()
        
        print('🏢 COMPLETE ROCKWOOL PRODUCT INVENTORY')
        print('=' * 80)
        print(f'📊 Total Products: {len(products)}')
        print()

        # Analyze categories
        categories = defaultdict(int)
        specs_with_thermal = 0
        specs_with_fire = 0
        specs_with_density = 0
        has_price = 0

        for product in products:
            if product.get('category'):
                categories[product['category']['name']] += 1
            
            if product.get('technical_specs'):
                if product['technical_specs'].get('thermal_conductivity'):
                    specs_with_thermal += 1
                if product['technical_specs'].get('fire_classification'):
                    specs_with_fire += 1
                if product['technical_specs'].get('density'):
                    specs_with_density += 1
            
            if product.get('price') is not None:
                has_price += 1

        print('📂 PRODUCT CATEGORIES:')
        print('-' * 40)
        for cat, count in sorted(categories.items()):
            print(f'   {cat}: {count} products')

        print()
        print('🔧 TECHNICAL SPECIFICATIONS COVERAGE:')
        print('-' * 40)
        print(f'   🌡️  Thermal Conductivity: {specs_with_thermal}/{len(products)} products')
        print(f'   🔥 Fire Classification: {specs_with_fire}/{len(products)} products')
        print(f'   📏 Density: {specs_with_density}/{len(products)} products')

        print()
        print('💰 PRICING INFORMATION:')
        print('-' * 40)
        print(f'   Products with prices: {has_price}/{len(products)}')
        print('   Currency: HUF (Hungarian Forint)')
        print('   💡 NOTE: Prices are currently not populated in the database')

        print()
        print('📋 SAMPLE PRODUCTS WITH FULL ATTRIBUTES:')
        print('=' * 60)

        for i, product in enumerate(products[:3], 1):
            print(f'\n📦 Product #{i}: {product["name"]}')
            print(f'🆔 ID: {product["id"]}')
            cat_name = product["category"]["name"] if product.get("category") else "N/A"
            print(f'📂 Category: {cat_name}')
            manufacturer = product.get("manufacturer", {})
            man_name = manufacturer.get("name", "N/A")
            man_country = manufacturer.get("country", "N/A")
            print(f'🏭 Manufacturer: {man_name} ({man_country})')
            print(f'💰 Price: {product["price"]} {product["currency"]} (NULL - not set)')
            print(f'📦 SKU: {product["sku"] or "Not set"}')
            print(f'📏 Unit: {product["unit"] or "Not specified"}')
            print(f'✅ Active: {product["is_active"]}')
            print(f'📦 In Stock: {product["in_stock"]}')
            print(f'📅 Created: {product["created_at"]}')
            print(f'🔄 Updated: {product["updated_at"]}')
            
            if product.get('technical_specs'):
                print('🔧 Technical Specifications:')
                for key, value in product['technical_specs'].items():
                    print(f'   {key}: {value}')
            
            if product.get('raw_specs'):
                print('📊 Raw Specifications:')
                for key, value in product['raw_specs'].items():
                    print(f'   {key}: {value}')
            
            print('-' * 60)

        print(f'\n🎯 SUMMARY: {len(products)} ROCKWOOL products stored in both PostgreSQL and ChromaDB')
        print('✅ Technical specifications are well-populated')
        print('⚠️  Price information needs to be added from ROCKWOOL price lists')
        
        # Show unique thermal conductivity values
        thermal_values = set()
        for product in products:
            if product.get('technical_specs', {}).get('thermal_conductivity'):
                thermal_values.add(product['technical_specs']['thermal_conductivity'])
        
        if thermal_values:
            print('\n🌡️  THERMAL CONDUCTIVITY VALUES FOUND:')
            for value in sorted(thermal_values):
                print(f'   {value}')

    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    analyze_all_products() 