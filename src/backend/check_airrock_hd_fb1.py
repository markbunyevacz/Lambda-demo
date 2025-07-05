#!/usr/bin/env python3
"""
Airrock HD FB1 termék adatainak ellenőrzése
"""

from app.database import SessionLocal
from app.models.product import Product

def check_airrock_hd_fb1():
    """Ellenőrzi az Airrock HD FB1 termék adatait"""
    
    session = SessionLocal()
    try:
        # Airrock HD FB1 termék keresése
        product = session.query(Product).filter(Product.name.like('%Airrock HD FB1%')).first()
        
        if product:
            print('📋 CLAUDE 4 SONNET EREDMÉNYE:')
            print(f'   🏷️  Termék név: {product.name}')
            print(f'   📝 Leírás: {product.description}')
            print('   🔧 Műszaki adatok:')
            if product.technical_specs:
                for key, value in product.technical_specs.items():
                    if isinstance(value, dict):
                        val = value.get('value', 'N/A')
                        unit = value.get('unit', '')
                        print(f'      - {key}: {val} {unit}')
                    else:
                        print(f'      - {key}: {value}')
            else:
                print('      ❌ Nincsenek műszaki adatok')
            
            # Teljes szöveg ellenőrzése
            text_length = len(product.full_text_content or "")
            print(f'\n   📄 Teljes szöveg hossza: {text_length} karakter')
            
            if product.full_text_content:
                print('   📖 Szöveg előnézet (első 500 karakter):')
                preview = product.full_text_content[:500]
                print(f'   {preview}...')
            else:
                print('   ❌ Nincs teljes szöveg!')
        else:
            print('❌ Airrock HD FB1 termék nem található')
            
    except Exception as e:
        print(f'❌ Hiba: {e}')
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == '__main__':
    check_airrock_hd_fb1() 