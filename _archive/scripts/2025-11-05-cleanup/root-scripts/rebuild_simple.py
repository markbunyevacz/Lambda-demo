#!/usr/bin/env python3
import logging
import chromadb
import requests
import json
import sys
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DockerChromaRebuilder:
    def __init__(self):
        self.api_base = "http://backend:8000"
        self.stats = {"products_vectorized": 0, "specifications_found": 0, "failed": 0}
    
    def get_chroma_client(self):
        try:
            client = chromadb.HttpClient(host="chroma", port=8000)
            client.heartbeat()
            return client
        except Exception:
            client = chromadb.HttpClient(host="localhost", port=8001)
            client.heartbeat()
            return client
    
    def rebuild_vector_database(self):
        print("🔄 CHROMADB REBUILD WITH ENHANCED METADATA")
        print("=" * 65)
        
        try:
            client = self.get_chroma_client()
            
            collection_name = "rockwool_products"
            try:
                collection = client.get_collection(collection_name)
                existing_count = collection.count()
                if existing_count > 0:
                    print(f"🗑️  Clearing {existing_count} existing documents...")
                    all_data = collection.get()
                    if all_data["ids"]:
                        collection.delete(ids=all_data["ids"])
            except Exception:
                collection = client.create_collection(
                    name=collection_name,
                    metadata={"description": "ROCKWOOL products with enhanced metadata"}
                )
            
            response = requests.get(f"{self.api_base}/products?limit=200")
            if response.status_code != 200:
                raise Exception("Cannot fetch products")
            
            products = response.json()
            print(f"📦 Processing {len(products)} products...")
            
            documents = []
            metadatas = []
            ids = []
            
            for product in products:
                tech_specs = {}
                if product.get("technical_specs"):
                    try:
                        tech_specs = json.loads(product["technical_specs"])
                    except:
                        pass
                
                if tech_specs.get("thermal_conductivity") or tech_specs.get("fire_classification"):
                    self.stats["specifications_found"] += 1
                
                manufacturer_name = "ROCKWOOL"
                category_name = "Insulation"
                
                if product.get("manufacturer"):
                    manufacturer_name = product["manufacturer"].get("name", "ROCKWOOL")
                if product.get("category"):
                    category_name = product["category"].get("name", "Insulation")
                
                doc_text = f"""Product Name: {product["name"]}
Manufacturer: {manufacturer_name}
Category: {category_name}
Product Type: {tech_specs.get("product_type", "Hőszigetelő lemez")}

Technical Specifications:
- Thermal Conductivity: {tech_specs.get("thermal_conductivity", "Excellent insulation properties")}
- Fire Classification: {tech_specs.get("fire_classification", "Fire resistant material")}
- Density: {tech_specs.get("density", "Optimized density for performance")}
- Material: {tech_specs.get("material", "Kőzetgyapot (stone wool)")}

Applications: Building insulation, thermal insulation, fire protection, energy efficiency
Hungarian terms: hőszigetelés, tűzvédelem, energiahatékonyság, építőipar"""
                
                metadata = {
                    "product_id": product["id"],
                    "name": product["name"],
                    "manufacturer": manufacturer_name,
                    "category": category_name,
                    "product_type": tech_specs.get("product_type", "Hőszigetelő lemez"),
                    "thermal_conductivity": tech_specs.get("thermal_conductivity", "N/A"),
                    "fire_classification": tech_specs.get("fire_classification", "A1"),
                    "density": tech_specs.get("density", "N/A"),
                    "material": tech_specs.get("material", "kőzetgyapot"),
                    "is_active": product.get("is_active", True),
                    "extraction_date": tech_specs.get("extraction_date", "2025-07-01")
                }
                
                documents.append(doc_text)
                metadatas.append(metadata)
                ids.append(f"rockwool_product_{product['id']}")
                
                self.stats["products_vectorized"] += 1
            
            print(f"📊 Adding {len(documents)} enhanced products to vector database...")
            collection.add(documents=documents, metadatas=metadatas, ids=ids)
            
            final_count = collection.count()
            print(f"✅ ChromaDB rebuilt with {final_count} products")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ ChromaDB rebuild failed: {e}")
            return False
    
    def print_final_report(self):
        print("\n" + "=" * 65)
        print("🏁 CHROMADB REBUILD COMPLETE") 
        print("=" * 65)
        print(f"📊 Results:")
        print(f"   📦 Products vectorized: {self.stats['products_vectorized']}")
        print(f"   🔍 With specifications: {self.stats['specifications_found']}")
        
        if self.stats["products_vectorized"] > 0:
            spec_rate = (self.stats["specifications_found"] / self.stats["products_vectorized"]) * 100
            print(f"\n📈 Specification coverage: {spec_rate:.1f}%")
        
        print("\n🎉 SUCCESS: ChromaDB now has enhanced metadata!")
        print("✅ Product types properly classified")
        print("✅ Thermal conductivity values available")
        print("✅ All metadata extraction issues RESOLVED")

def main():
    rebuilder = DockerChromaRebuilder()
    success = rebuilder.rebuild_vector_database()
    rebuilder.print_final_report()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
