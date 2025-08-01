from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config.settings import settings

# Database engine configuration using centralized settings
engine = create_engine(
    settings.database.url,
    echo=settings.database.echo_sql,
    # A connect_args csak SQLite-hoz szükséges
    connect_args={"check_same_thread": False} if "sqlite" in settings.database.url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Dependency
def get_db():
    """Database session dependency for FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()