#!/usr/bin/env python3
"""
PostgreSQL → ChromaDB szinkronizálás
"""

from app.database import SessionLocal
from app.models.product import Product
import chromadb

def sync_postgresql_to_chromadb():
    """Szinkronizálja a PostgreSQL termékeket a ChromaDB-be"""
    
    session = SessionLocal()
    client = chromadb.HttpClient(host='chroma', port=8000)
    
    try:
        # Termékek lekérése PostgreSQL-ből
        products = session.query(Product).all()
        print(f'📊 PostgreSQL termékek: {len(products)}')
        
        # ChromaDB collection
        collection = client.get_or_create_collection(
            name='pdf_products',
            metadata={'description': 'ROCKWOOL PDF products'}
        )
        
        # Termékek feltöltése ChromaDB-be
        documents = []
        metadatas = []
        ids = []
        
        for product in products:
            # Dokumentum szöveg összeállítása
            doc_text = f"{product.name}\n{product.description or ''}"
            if product.technical_specs:
                for key, value in product.technical_specs.items():
                    if isinstance(value, dict):
                        val = value.get('value', '')
                        unit = value.get('unit', '')
                        doc_text += f"\n{key}: {val} {unit}"
                    else:
                        doc_text += f"\n{key}: {value}"
            
            documents.append(doc_text)
            metadatas.append({
                'product_id': product.id,
                'name': product.name,
                'category': product.category.name if product.category else 'Unknown',
                'doc_type': 'Termék'
            })
            ids.append(f'product_{product.id}')
        
        # Feltöltés ChromaDB-be
        if documents:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f'✅ {len(documents)} termék feltöltve ChromaDB-be!')
        
        # Ellenőrzés
        final_count = collection.count()
        print(f'📊 ChromaDB végső állapot: {final_count} dokumentum')
        
    except Exception as e:
        print(f'❌ Hiba: {e}')
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == '__main__':
    sync_postgresql_to_chromadb() 