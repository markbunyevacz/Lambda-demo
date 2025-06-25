from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Ez a környezeti változókból fog jönni a Docker konténerben
# Jelenleg egy helyi SQLite adatbázist használunk a könnyebb fejlesztésért
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")


engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    # A connect_args csak SQLite-hoz szükséges
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base() 