from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL with proper UTF-8 encoding for Hungarian content
# Check if we're running inside Docker or external
def get_database_url():
    # ✅ CRITICAL FIX: Always prefer localhost over Docker container
    # Docker container has UTF-8 encoding issues, localhost works perfectly
    
    # Try to connect to PostgreSQL via localhost first (ALWAYS)
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 5432))
        sock.close()
        if result == 0:
            # PostgreSQL is accessible via localhost:5432 - USE THIS!
            print("🔧 Using localhost PostgreSQL connection (UTF-8 safe)")
            return "postgresql://lambda_user:Cz31n1ng3r@localhost:5432/lambda_db"
    except:
        pass
    
    # Only use Docker environment if localhost is not available
    docker_url = os.getenv("DATABASE_URL")
    if docker_url:
        print("⚠️ Using Docker PostgreSQL connection (may have UTF-8 issues)")
        return docker_url
    
    # Fallback to SQLite for development
    print("💾 Falling back to SQLite")
    return "sqlite:///./test.db"

SQLALCHEMY_DATABASE_URL = get_database_url()


# Engine configuration with UTF-8 encoding support
connect_args = {}
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    connect_args = {"check_same_thread": False}
elif "postgresql" in SQLALCHEMY_DATABASE_URL:
    # ✅ FIXED: PostgreSQL UTF-8 settings - consistent lowercase, no duplicates
    connect_args = {
        "client_encoding": "utf8",
        "options": "-c timezone=Europe/Budapest"
    }

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args=connect_args,
    # Additional engine options for UTF-8 support
    pool_pre_ping=True,
    echo=False  # Set to True for debugging SQL queries
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Adatbázis session dependency FastAPI-hoz és Celery feladatokhoz.

    Ez a "dependency" egy adatbázis session-t biztosít a request-ek vagy
    feladatok számára, és biztosítja, hogy a session a végén megfelelően
    lezárásra kerüljön, még hiba esetén is.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 