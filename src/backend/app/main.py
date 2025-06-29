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

from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional

# Helyi importok
from . import models, schemas
from .database import get_db, engine
from .scraper.api_endpoints import scraper_router
from .celery_tasks.scraping_tasks import (
    run_datasheet_scraping_task,
    run_brochure_scraping_task,
)

# Adatbázis táblák létrehozása az alkalmazás indításakor
models.Base.metadata.create_all(bind=engine)

# FastAPI alkalmazás példány létrehozása
app = FastAPI(
    title="Lambda.hu API",
    description="API for the Lambda.hu building material intelligence system.",
    version="1.0.0"
)

# CORS middleware konfigurálása a frontend integrációhoz
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Scraper API routes hozzáadása
app.include_router(scraper_router)

# API v1 Router
api_v1_router = APIRouter(prefix="/api/v1")

@api_v1_router.post("/scrape", status_code=202)
async def trigger_scraping(scrape_request: schemas.ScrapeRequest):
    """
    Triggers a background scraping task.
    - **scraper_type**: 'datasheet' or 'brochure'.
    """
    if scrape_request.scraper_type == "datasheet":
        task = run_datasheet_scraping_task.delay()
    elif scrape_request.scraper_type == "brochure":
        task = run_brochure_scraping_task.delay()
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid scraper_type. Use 'datasheet' or 'brochure'.",
        )
    return {"message": "Scraping task accepted.", "task_id": task.id}

@api_v1_router.get("/products", response_model=List[schemas.Product])
def read_products(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    products = db.query(models.Product).offset(skip).limit(limit).all()
    return products

@api_v1_router.get("/categories", response_model=List[schemas.Category])
def read_categories(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    categories = db.query(models.Category).offset(skip).limit(limit).all()
    return categories

app.include_router(api_v1_router)

# Root endpoint for basic health check
@app.get("/")
async def root():
    return {"message": "Lambda.hu API is running."}

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
    categories = db.query(models.Category).all()
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
        parent = db.query(models.Category).filter(
            models.Category.id == parent_id
        ).first()
        if not parent:
            raise HTTPException(
                status_code=404, 
                detail="Szülő kategória nem található"
            )
    
    # Új kategória létrehozása
    new_category = models.Category(
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
    manufacturers = db.query(models.Manufacturer).all()
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
    new_manufacturer = models.Manufacturer(
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
    query = db.query(models.Product)
    
    # Szűrők alkalmazása ha meg vannak adva
    if category_id:
        query = query.filter(models.Product.category_id == category_id)
    if manufacturer_id:
        query = query.filter(
            models.Product.manufacturer_id == manufacturer_id
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
        cat = db.query(models.Category).filter(
            models.Category.id == category_id
        ).first()
        if not cat:
            raise HTTPException(
                status_code=404, 
                detail="Kategória nem található"
            )
    
    # Gyártó validálása  
    if manufacturer_id:
        mfr = db.query(models.Manufacturer).filter(
            models.Manufacturer.id == manufacturer_id
        ).first()
        if not mfr:
            raise HTTPException(
                status_code=404, 
                detail="Gyártó nem található"
            )
    
    # Új termék létrehozása
    new_product = models.Product(
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