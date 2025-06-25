"""
Lambda.hu Építőanyag AI - Backend API

Ez a fájl tartalmazza a FastAPI alkalmazás fő belépési pontját.
Az alkalmazás RESTful API-t biztosít az építőanyag adatok kezeléséhez.

Főbb funkciók:
- Kategória menedzsment (hierarchikus struktúra)
- Gyártó adatok kezelése  
- Termék információk tárolása és lekérdezése
- CORS támogatás frontend integrációhoz

Technológiák:
- FastAPI: Modern, gyors Python web framework
- SQLAlchemy: ORM adatbázis műveletekhez
- PostgreSQL: Relációs adatbázis
- Redis: Cache layer (jövőbeli használatra)
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional

# Helyi importok
from .database import get_db, engine
from .models import category, manufacturer, product
from .scraper.api_endpoints import scraper_router

# Adatbázis táblák létrehozása az alkalmazás indításakor
category.Base.metadata.create_all(bind=engine)
manufacturer.Base.metadata.create_all(bind=engine)  
product.Base.metadata.create_all(bind=engine)

# FastAPI alkalmazás példány létrehozása
app = FastAPI(
    title="Lambda.hu Építőanyag AI API",
    description="RESTful API építőanyag adatok kezeléséhez "
               "AI-alapú keresési rendszerhez",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI endpoint
    redoc_url="/redoc"  # ReDoc dokumentáció endpoint
)

# CORS middleware konfigurálása a frontend integrációhoz
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Minden HTTP metódus engedélyezése
    allow_headers=["*"],  # Minden header engedélyezése
)

# Scraper API routes hozzáadása
app.include_router(scraper_router)

@app.get("/")
async def root():
    """
    Alapvető health check endpoint
    
    Returns:
        dict: Alapvető információ az API-ról
    """
    return {
        "message": "Lambda.hu Építőanyag AI Backend API", 
        "version": "1.0.0",
        "status": "running"
    }

# ==================== KATEGÓRIA ENDPOINTS ====================

@app.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    """
    Összes kategória lekérdezése hierarchikus struktúrával
    
    Args:
        db (Session): Adatbázis session dependency injection
        
    Returns:
        List[dict]: Kategóriák listája to_dict() formátumban
    """
    categories = db.query(category.Category).all()
    return [cat.to_dict() for cat in categories]

@app.post("/categories")  
async def create_category(
    name: str, 
    description: Optional[str] = None,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Új kategória létrehozása
    
    Args:
        name (str): Kategória neve (kötelező)
        description (str, optional): Kategória leírása
        parent_id (int, optional): Szülő kategória ID 
                                 (hierarchikus struktúrához)
        db (Session): Adatbázis session
        
    Returns:
        dict: Létrehozott kategória adatai
        
    Raises:
        HTTPException: Ha a parent_id nem létező kategóriára mutat
    """
    # Szülő kategória validálása ha meg van adva
    if parent_id:
        parent = db.query(category.Category).filter(
            category.Category.id == parent_id
        ).first()
        if not parent:
            raise HTTPException(
                status_code=404, 
                detail="Szülő kategória nem található"
            )
    
    # Új kategória létrehozása
    new_category = category.Category(
        name=name,
        description=description, 
        parent_id=parent_id
    )
    
    # Adatbázisba mentés
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    return new_category.to_dict()

# ==================== GYÁRTÓ ENDPOINTS ====================

@app.get("/manufacturers")
async def get_manufacturers(db: Session = Depends(get_db)):
    """
    Összes gyártó lekérdezése
    
    Args:
        db (Session): Adatbázis session
        
    Returns:
        List[dict]: Gyártók listája
    """
    manufacturers = db.query(manufacturer.Manufacturer).all()
    return [mfr.to_dict() for mfr in manufacturers]

@app.post("/manufacturers")
async def create_manufacturer(
    name: str,
    contact_info: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Új gyártó létrehozása
    
    Args:
        name (str): Gyártó neve
        contact_info (str, optional): Kapcsolattartási információ
        db (Session): Adatbázis session
        
    Returns:
        dict: Létrehozott gyártó adatai
    """
    new_manufacturer = manufacturer.Manufacturer(
        name=name,
        contact_info=contact_info
    )
    
    db.add(new_manufacturer)
    db.commit() 
    db.refresh(new_manufacturer)
    
    return new_manufacturer.to_dict()

# ==================== TERMÉK ENDPOINTS ====================

@app.get("/products")
async def get_products(
    limit: int = 100,
    offset: int = 0,
    category_id: Optional[int] = None,
    manufacturer_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Termékek lekérdezése szűrési és lapozási lehetőségekkel
    
    Args:
        limit (int): Maximális eredmények száma (default: 100)
        offset (int): Elhagyandó eredmények száma lapozáshoz (default: 0)
        category_id (int, optional): Szűrés kategória szerint
        manufacturer_id (int, optional): Szűrés gyártó szerint
        db (Session): Adatbázis session
        
    Returns:
        List[dict]: Termékek listája a megadott szűrőkkel
    """
    query = db.query(product.Product)
    
    # Szűrők alkalmazása ha meg vannak adva
    if category_id:
        query = query.filter(product.Product.category_id == category_id)
    if manufacturer_id:
        query = query.filter(
            product.Product.manufacturer_id == manufacturer_id
        )
    
    # Lapozás alkalmazása
    products = query.offset(offset).limit(limit).all()
    
    return [prod.to_dict() for prod in products]

@app.post("/products")
async def create_product(
    name: str,
    description: Optional[str] = None,
    price: Optional[float] = None,
    category_id: Optional[int] = None,
    manufacturer_id: Optional[int] = None,
    technical_specs: Optional[dict] = None,
    db: Session = Depends(get_db)
):
    """
    Új termék létrehozása
    
    Args:
        name (str): Termék neve
        description (str, optional): Termék leírása
        price (float, optional): Termék ára
        category_id (int, optional): Kategória ID
        manufacturer_id (int, optional): Gyártó ID  
        technical_specs (dict, optional): Technikai specifikációk 
                                        JSON formátumban
        db (Session): Adatbázis session
        
    Returns:
        dict: Létrehozott termék adatai
        
    Raises:
        HTTPException: Ha a kategória vagy gyártó ID nem létezik
    """
    # Kategória validálása
    if category_id:
        cat = db.query(category.Category).filter(
            category.Category.id == category_id
        ).first()
        if not cat:
            raise HTTPException(
                status_code=404, 
                detail="Kategória nem található"
            )
    
    # Gyártó validálása  
    if manufacturer_id:
        mfr = db.query(manufacturer.Manufacturer).filter(
            manufacturer.Manufacturer.id == manufacturer_id
        ).first()
        if not mfr:
            raise HTTPException(
                status_code=404, 
                detail="Gyártó nem található"
            )
    
    # Új termék létrehozása
    new_product = product.Product(
        name=name,
        description=description,
        price=price,
        category_id=category_id,
        manufacturer_id=manufacturer_id,
        technical_specs=technical_specs or {}
    )
    
    # Adatbázisba mentés
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    return new_product.to_dict()

# ==================== ALKALMAZÁS STÁTUSZ ====================

@app.get("/health")
async def health_check():
    """
    Részletes health check endpoint monitoring célokra
    
    Returns:
        dict: Alkalmazás állapot információk
    """
    return {
        "status": "healthy",
        "database": "connected", 
        "api_version": "1.0.0",
        "environment": "development"
    } 