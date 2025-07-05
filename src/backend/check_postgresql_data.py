#!/usr/bin/env python3
"""
PostgreSQL adatok részletes ellenőrzése
"""

from app.database import SessionLocal
from app.models.product import Product

def check_postgresql_data():
    """Ellenőrzi a PostgreSQL-ben lévő termékadatokat"""
    
    session = SessionLocal()
    try:
        # Összes termék száma
        total_count = session.query(Product).count()
        print(f'📊 Összesen {total_count} termék a PostgreSQL-ben\n')
        
        # Első 3 termék részletesen
        products = session.query(Product).limit(3).all()
        
        for i, product in enumerate(products, 1):
            print(f'📋 TERMÉK {i}: {product.name}')
            print(f'   🏷️  SKU: {product.sku}')
            print(f'   📝 Leírás: {product.description}')
            
            if product.technical_specs:
                print(f'   🔧 Műszaki adatok ({len(product.technical_specs)} db):')
                for key, value in product.technical_specs.items():
                    if isinstance(value, dict):
                        val = value.get('value', 'N/A')
                        unit = value.get('unit', '')
                        print(f'      - {key}: {val} {unit}')
                    else:
                        print(f'      - {key}: {value}')
            else:
                print('   ❌ Nincsenek műszaki adatok!')
            
            # Teljes szöveg ellenőrzése
            text_length = len(product.full_text_content or "")
            print(f'   📄 Teljes szöveg hossza: {text_length} karakter')
            
            if product.full_text_content:
                preview = product.full_text_content[:200]
                if len(product.full_text_content) > 200:
                    preview += '...'
                print(f'   📖 Szöveg előnézet: {preview}')
            else:
                print('   ❌ Nincs teljes szöveg!')
            
            print('-' * 80)
            
        # Statisztikák
        print('\n📈 STATISZTIKÁK:')
        
        # Műszaki adatokkal rendelkező termékek
        with_specs = session.query(Product).filter(Product.technical_specs.isnot(None)).count()
        print(f'   🔧 Műszaki adatokkal: {with_specs}/{total_count} termék')
        
        # Teljes szöveggel rendelkező termékek  
        with_text = session.query(Product).filter(Product.full_text_content.isnot(None)).count()
        print(f'   📄 Teljes szöveggel: {with_text}/{total_count} termék')
        
        # Leírással rendelkező termékek
        with_desc = session.query(Product).filter(Product.description.isnot(None)).count()
        print(f'   📝 Leírással: {with_desc}/{total_count} termék')
        
    except Exception as e:
        print(f'❌ Hiba: {e}')
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == '__main__':
    check_postgresql_data() 