#!/usr/bin/env python3
"""
RAG Pipeline Initialization
Initializes vector database with ROCKWOOL product data for semantic search
"""

import logging
import chromadb
from pathlib import Path
import sys
from sqlalchemy.orm import sessionmaker
import os
from sqlalchemy import create_engine

# Add the current directory to Python path for imports
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

# Import database models and connection
from app.models.product import Product

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_chroma_client():
    """Get ChromaDB client with fallback connection logic"""
    # Try Docker internal network first (when running inside Docker)
    try:
        logger.info("Trying Docker internal connection (chroma:8000)...")
        client = chromadb.HttpClient(host="chroma", port=8000)
        client.heartbeat()  # Test connection
        logger.info("✅ Connected to ChromaDB via Docker network")
        return client
    except Exception as e:
        logger.info(f"Docker network connection failed: {e}")
        
    # Fallback to localhost (when running outside Docker)
    try:
        logger.info("Trying localhost connection (localhost:8001)...")
        client = chromadb.HttpClient(host="localhost", port=8001)
        client.heartbeat()  # Test connection
        logger.info("✅ Connected to ChromaDB via localhost")
        return client
    except Exception as e:
        logger.error(f"Both connection attempts failed: {e}")
        raise

def initialize_rag_pipeline():
    """Initialize the RAG pipeline with ROCKWOOL product data"""
    
    logger.info("--- Starting RAG Pipeline Initialization ---")
    
    try:
        # Connect to ChromaDB
        logger.info("Connecting to ChromaDB...")
        client = get_chroma_client()
        
        # Create or get collection for ROCKWOOL products
        collection_name = "rockwool_products"
        logger.info(f"Creating/accessing collection: {collection_name}")
        
        try:
            collection = client.get_collection(collection_name)
            logger.info(f"✅ Found existing collection: {collection_name}")
        except Exception:
            collection = client.create_collection(
                name=collection_name,
                metadata={"description": "ROCKWOOL building insulation products"}
            )
            logger.info(f"✅ Created new collection: {collection_name}")
        
        # Connect to PostgreSQL database
        logger.info("Connecting to PostgreSQL database...")
        DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
        if "postgresql" in DATABASE_URL:
            DATABASE_URL += "?client_encoding=utf8"
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Fetch all ROCKWOOL products from database
            logger.info("Fetching ROCKWOOL products from database...")
            products = db.query(Product).filter(
                Product.manufacturer.has(name="ROCKWOOL")
            ).all()
            
            logger.info(f"Found {len(products)} ROCKWOOL products in database")
            
            if not products:
                logger.warning("No ROCKWOOL products found in database!")
                logger.info("Please ensure database integration is complete")
                return
            
            # Prepare documents for vectorization
            documents = []
            metadatas = []
            ids = []
            
            for product in products:
                # Extract technical specs from JSON
                tech_specs = product.technical_specs or {}
                
                # Create comprehensive document text for better semantic search
                doc_text = f"""
                Product Name: {product.name}
                Manufacturer: ROCKWOOL
                Category: {product.category.name if product.category else 'Insulation'}
                SKU: {product.sku or 'N/A'}
                
                Technical Specifications:
                - Thermal Conductivity: {tech_specs.get('thermal_conductivity', 'N/A')} W/mK
                - Fire Classification: {tech_specs.get('fire_classification', 'N/A')}
                - Density: {tech_specs.get('density', 'N/A')} kg/m³
                - Compressive Strength: {tech_specs.get('compressive_strength', 'N/A')}
                - Temperature Range: {tech_specs.get('temperature_range', 'N/A')}
                
                Description: {product.description or 'ROCKWOOL building insulation product'}
                Full Text Content: {product.full_text_content or ''}
                
                Price: {product.get_display_price()}
                Unit: {product.unit or 'N/A'}
                
                Applications: Building insulation, thermal insulation, fire protection
                """.strip()
                
                # Create metadata for filtering and retrieval
                metadata = {
                    "product_id": product.id,
                    "name": product.name,
                    "manufacturer": "ROCKWOOL",
                    "category": (product.category.name if product.category 
                               else "Insulation"),
                    "is_active": product.is_active,
                    "in_stock": product.in_stock,
                }
                
                # Add non-null optional fields
                if product.sku:
                    metadata["sku"] = product.sku
                if product.price:
                    metadata["price"] = float(product.price)
                if product.currency:
                    metadata["currency"] = product.currency
                if product.unit:
                    metadata["unit"] = product.unit
                if product.source_url:
                    metadata["source_url"] = product.source_url
                if product.created_at:
                    metadata["created_at"] = product.created_at.isoformat()
                if product.updated_at:
                    metadata["updated_at"] = product.updated_at.isoformat()
                    
                # Add technical specs if available
                if tech_specs.get('thermal_conductivity'):
                    metadata["thermal_conductivity"] = tech_specs['thermal_conductivity']
                if tech_specs.get('fire_classification'):
                    metadata["fire_classification"] = tech_specs['fire_classification']
                if tech_specs.get('density'):
                    metadata["density"] = tech_specs['density']
                if tech_specs.get('compressive_strength'):
                    metadata["compressive_strength"] = tech_specs['compressive_strength']
                if tech_specs.get('temperature_range'):
                    metadata["temperature_range"] = tech_specs['temperature_range']
                
                documents.append(doc_text)
                metadatas.append(metadata)
                ids.append(f"rockwool_product_{product.id}")
            
            # Add documents to ChromaDB collection
            logger.info(f"Adding {len(documents)} products to vector database...")
            
            # Clear existing data if any
            existing_count = collection.count()
            if existing_count > 0:
                logger.info(f"Clearing {existing_count} existing documents...")
                all_data = collection.get()
                if all_data['ids']:
                    collection.delete(ids=all_data['ids'])
                
            # Add new documents
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            # Verify the addition
            final_count = collection.count()
            logger.info(f"✅ Successfully added {final_count} products to vector database")
            
            # Test semantic search
            logger.info("Testing semantic search functionality...")
            test_results = collection.query(
                query_texts=["thermal insulation with low conductivity"],
                n_results=3
            )
            
            logger.info("🔍 Sample search results:")
            if test_results['documents'] and test_results['metadatas']:
                docs = test_results['documents'][0]
                metas = test_results['metadatas'][0]
                for i, (doc, metadata) in enumerate(zip(docs, metas)):
                    name = metadata.get('name', 'Unknown')
                    thermal = metadata.get('thermal_conductivity', 'N/A')
                    logger.info(f"  {i+1}. {name} (λ: {thermal} W/mK)")
            
            logger.info("✅ RAG Pipeline successfully initialized!")
            logger.info(f"Vector database ready with {final_count} ROCKWOOL products")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to initialize RAG pipeline: {e}")
        logger.error("Please ensure ChromaDB service is running and database is accessible.")
        raise
    
    logger.info("--- RAG Pipeline Initialization Finished ---")

if __name__ == "__main__":
    initialize_rag_pipeline() 