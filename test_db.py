import sys
from pathlib import Path
import chromadb
from sqlalchemy.orm import Session

# Add the project root to the Python path to resolve imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from src.backend.app.database import SessionLocal, engine
    from src.backend.app.models.product import Product  # Import a model to test query
    print("✅ Successfully imported database modules.")
except ImportError as e:
    print(f"❌ Failed to import database modules: {e}")
    sys.exit(1)

def check_postgresql_connection(db: Session):
    """Checks the connection to PostgreSQL by performing a simple query."""
    try:
        # Perform a simple query to check the connection
        product_count = db.query(Product).count()
        print(f"✅ PostgreSQL connection successful. Found {product_count} products.")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

def check_chromadb_connection():
    """Checks the connection to ChromaDB by creating a client and listing collections."""
    try:
        # ChromaDB client will try to connect to http://localhost:8001 by default,
        # which is the exposed port from the Docker container.
        chroma_client = chromadb.HttpClient(host='localhost', port=8001)
        collections = chroma_client.list_collections()
        collection_names = [c.name for c in collections]
        print(f"✅ ChromaDB connection successful. Found collections: {collection_names}")
        return True
    except Exception as e:
        print(f"❌ ChromaDB connection failed: {e}")
        return False

def main():
    print("🚀 Starting Docker service connection test...")

    # Test PostgreSQL
    print("\n--- Testing PostgreSQL ---")
    db_session = SessionLocal()
    pg_ok = False
    try:
        pg_ok = check_postgresql_connection(db_session)
    finally:
        db_session.close()

    # Test ChromaDB
    print("\n--- Testing ChromaDB ---")
    chroma_ok = check_chromadb_connection()

    print("\n--- Test Summary ---")
    if pg_ok and chroma_ok:
        print("✅✅✅ All services are reachable from the host machine!")
        print("PDF processing can proceed.")
    else:
        print("❌❌❌ One or more services are not reachable. Please check Docker setup.")
        sys.exit(1)


if __name__ == "__main__":
    main() 