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

from fastapi import FastAPI, Depends, HTTPException, APIRouter, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

# Helyi importok
from .database import Base, engine, get_db
# Import all models to ensure they are registered with SQLAlchemy's Base
from .models import manufacturer, category, product
from . import models, schemas

# RAG Search imports
import chromadb

# Import Celery app for task management
from .celery_app import celery_app
# Hibás, elavult router importjának eltávolítása
# from .scraper.api_endpoints import scraper_router
# Scraper imports commented out to avoid path resolution issues in Docker
# from .scrapers.rockwool_final.datasheet_scraper import RockwoolDirectScraper
# from .scrapers.rockwool_final.brochure_and_pricelist_scraper import RockwoolBrochureScraper

# Create the database tables
# This should be done only once, ideally managed with Alembic migrations
# in a real production environment.
Base.metadata.create_all(bind=engine)

# FastAPI alkalmazás példány létrehozása
app = FastAPI(
    title="Lambda.hu API",
    description="API for the Lambda.hu building material intelligence system.",
    version="1.0.0",
    redoc_url=None, # Disable redoc
)

# CORS middleware konfigurálása a frontend integrációhoz
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Scraper API routes hozzáadása
# app.include_router(scraper_router)

# API v1 Router
api_v1_router = APIRouter(prefix="/api/v1")

# --- Helper function for running scrapers ---
# Commented out to avoid Docker path resolution issues
# async def run_scraper_in_background(scraper_class):
#     """Initializes and runs a scraper instance."""
#     scraper = scraper_class()
#     await scraper.run()

# @api_v1_router.post("/scrape", status_code=202)
# async def trigger_scraping(
#     scrape_request: schemas.ScrapeRequest,
#     background_tasks: BackgroundTasks
# ):
#     """
#     Triggers a scraping task in the background without Celery.
#     """
#     if scrape_request.scraper_type == "datasheet":
#         background_tasks.add_task(run_scraper_in_background, RockwoolDirectScraper)
#         message = "Datasheet scraping task started in the background."
#     elif scrape_request.scraper_type == "brochure":
#         background_tasks.add_task(run_scraper_in_background, RockwoolBrochureScraper)
#         message = "Brochure scraping task started in the background."
#     else:
#         raise HTTPException(
#             status_code=400,
#             detail="Invalid scraper_type. Use 'datasheet' or 'brochure'.",
#         )
#     return {"message": message}

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

# Root endpoint for basic health check and redirect to search
@app.get("/", response_class=RedirectResponse)
async def root():
    """Redirects root to the main search interface."""
    return "/search"

# ==================== KATEGÓRIA ENDPOINTS ====================

@app.get("/categories", include_in_schema=False)
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

@app.post("/categories", include_in_schema=False)  
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

@app.get("/manufacturers", include_in_schema=False)
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

# ==================== RAG SEARCH ENDPOINTS ====================

def get_chroma_client():
    """Get ChromaDB client with fallback connection logic"""
    try:
        chroma_client = chromadb.HttpClient(host="chroma", port=8000)
        chroma_client.heartbeat()
        return chroma_client
    except Exception:
        try:
            chroma_client = chromadb.HttpClient(host="localhost", port=8001)
            chroma_client.heartbeat()
            return chroma_client
        except Exception as e:
            logging.error(f"ChromaDB connection failed: {e}")
            raise HTTPException(
                status_code=503, 
                detail=f"Kereső szolgáltatás nem elérhető: {e}"
            )

@app.get("/search", response_class=HTMLResponse, include_in_schema=False)
async def search_interface():
    """Simple HTML interface for RAG search"""
    html_content = """
    <!DOCTYPE html>
    <html lang="hu">
    <head>
        <title>Lambda.hu Intelligens Kereső</title>
        <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🏗️</text></svg>">
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; background-color: #f9f9f9; color: #333; }
            h1 { color: #2c3e50; }
            .search-container { display: flex; gap: 10px; margin: 20px 0; }
            .search-box { flex-grow: 1; padding: 15px; font-size: 16px; border: 1px solid #ccc; border-radius: 5px; }
            .search-box:focus { border-color: #007bff; outline: none; }
            .search-btn { padding: 15px 30px; font-size: 16px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
            .search-btn:hover { background: #0056b3; }
            .limit-selector { padding: 15px; font-size: 16px; border: 1px solid #ccc; border-radius: 5px; background-color: white; }
            .result { border: 1px solid #ddd; margin: 15px 0; padding: 15px; border-radius: 5px; background-color: white; transition: box-shadow 0.2s; }
            .result a { text-decoration: none; color: inherit; }
            .result-product:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); cursor: pointer; }
            .result-title { font-weight: 600; color: #007bff; font-size: 1.1em; }
            .result-category { color: #555; font-style: italic; margin: 4px 0; }
            .result-score { color: #28a745; font-size: 12px; font-weight: bold; }
            .result-type { float: right; font-size: 12px; background-color: #e9ecef; padding: 3px 8px; border-radius: 10px; color: #495057; }
            .loading { display: none; text-align: center; color: #666; margin: 20px; }
            .stats { background: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <h1>🏗️ Lambda.hu Intelligens Kereső</h1>
        <p>Keressen a teljes adatbázisban (<strong>167 termék és dokumentum</strong>) természetes nyelven.</p>
        
        <div class="search-container">
            <input type="text" id="searchQuery" class="search-box" placeholder="Keresés... pl. 'homlokzati kőzetgyapot' vagy 'tűzállóság'" />
            <select id="limitSelector" class="limit-selector">
                <option value="10">10</option>
                <option value="25" selected>25</option>
                <option value="50">50</option>
            </select>
            <button onclick="performSearch()" class="search-btn">Keresés</button>
        </div>
        
        <div class="loading" id="loading">🔍 Keresés az adatbázisban...</div>
        <div id="searchStats" class="stats" style="display: none;"></div>
        <div id="searchResults"></div>
        
        <script>
            async function performSearch() {
                const query = document.getElementById('searchQuery').value;
                if (!query.trim()) return;

                const limit = parseInt(document.getElementById('limitSelector').value, 10);
                
                document.getElementById('loading').style.display = 'block';
                document.getElementById('searchResults').innerHTML = '';
                document.getElementById('searchStats').style.display = 'none';
                
                try {
                    const response = await fetch('/search/rag', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query: query, limit: limit })
                    });
                    
                    if (!response.ok) {
                        throw new Error(`A szerver hibát adott: ${response.statusText}`);
                    }

                    const data = await response.json();
                    
                    document.getElementById('loading').style.display = 'none';
                    
                    // Show stats
                    document.getElementById('searchStats').innerHTML = 
                        `📊 <strong>${data.total_results}</strong> találat a(z) <strong>${data.collection_size}</strong> adatbázis elem között a következőre: "<em>${data.query}</em>"`;
                    document.getElementById('searchStats').style.display = 'block';
                    
                    // Show results
                    const resultsDiv = document.getElementById('searchResults');
                    if (!data.results || data.results.length === 0) {
                        resultsDiv.innerHTML = '<div class="result">Nincs találat.</div>';
                    } else {
                        resultsDiv.innerHTML = data.results.map(result => {
                            const isProduct = result.metadata.doc_type === 'Termék';
                            const link = isProduct ? `/products/${result.metadata.product_id}/view` : '#';
                            const resultClass = isProduct ? 'result result-product' : 'result';
                            const title_attr = isProduct ? 'Kattintson a részletekért' : 'Ez egy dokumentum, nem kattintható';

                            return `
                            <div class="${resultClass}" ${isProduct ? `onclick="window.open('${link}', '_blank')"` : ''} title="${title_attr}">
                                <a href="${link}" target="_blank" onclick="event.stopPropagation()">
                                    <span class="result-type">${result.metadata.doc_type}</span>
                                    <div class="result-title">${result.rank}. ${result.name}</div>
                                    <div class="result-category">Kategória: ${result.category}</div>
                                    <div class="result-score">Hasonlóság: ${Math.max(0, result.similarity_score * 100).toFixed(1)}%</div>
                                    <div style="margin-top: 10px;">${result.description}</div>
                                </a>
                            </div>
                            `;
                        }).join('');
                    }
                } catch (error) {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('searchResults').innerHTML = 
                        '<div class="result" style="color: red;">Hiba történt a keresés során: ' + error.message + '</div>';
                }
            }
            
            // Allow Enter key to search
            document.getElementById('searchQuery').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') performSearch();
            });
        </script>
    </body>
    </html>
    """
    return html_content

@app.post("/search/rag", summary="Perform a RAG search")
async def rag_search(request: schemas.SearchRequest, db: Session = Depends(get_db)):
    """
    Végrehajt egy szemantikus keresést a vektor adatbázisban (ChromaDB)
    a felhasználói bevitelen alapulva.
    
    Ez a végpont a fő kereső funkciót szolgálja ki.
    """
    try:
        client = get_chroma_client()
        collection = client.get_collection("pdf_products")
        
        results = collection.query(
            query_texts=[request.query],
            n_results=request.limit
        )
        
        search_results = []
        if results['documents'] and results['documents'][0]:
            # Get product descriptions from postgres to show clean data
            product_ids = [meta['product_id'] for meta in results['metadatas'][0] if meta.get('product_id')]
            products_from_db = db.query(models.Product).filter(models.Product.id.in_(product_ids)).all()
            products_map = {p.id: p for p in products_from_db}

            for i, (doc, meta, distance) in enumerate(zip(
                results['documents'][0], 
                results['metadatas'][0],
                results['distances'][0]
            )):
                product = products_map.get(meta.get('product_id'))
                clean_description = product.description if product and product.description else "Nincs részletes leírás."
                
                search_results.append({
                    "rank": i + 1,
                    "name": meta.get('name', 'Ismeretlen termék'),
                    "category": meta.get('category', 'N/A'),
                    "description": clean_description[:300] + "..." if len(clean_description) > 300 else clean_description,
                    "full_content": doc, # Keep the vectorized content for debugging if needed
                    "metadata": meta,
                    "similarity_score": 1 - distance  # Convert L2 distance to similarity
                })
        
        return {
            "query": request.query,
            "total_results": len(search_results),
            "collection_size": collection.count(),
            "results": search_results
        }
        
    except Exception as e:
        logging.error(f"RAG search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )

# ==================== PRODUCT DETAIL VIEW ====================
@app.get("/products/{product_id}/view", response_class=HTMLResponse, include_in_schema=False)
async def get_product_view(product_id: int, db: Session = Depends(get_db)):
    """Renders a simple HTML page for a single product."""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="A termék nem található")

    specs_html = "<h3>Nincsenek megadva</h3>"
    if product.technical_specs and isinstance(product.technical_specs, dict):
        specs_html = "<ul>"
        for key, value in product.technical_specs.items():
            specs_html += f"<li><strong>{key}:</strong> {value}</li>"
        specs_html += "</ul>"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="hu">
    <head>
        <title>{product.name}</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; background-color: #f9f9f9; color: #333; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
            h2 {{ color: #34495e; }}
            p {{ line-height: 1.6; }}
            .specs {{ background-color: white; border: 1px solid #ddd; padding: 20px; border-radius: 5px; }}
            .specs ul {{ list-style-type: none; padding-left: 0; }}
            .specs li {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
            .specs li:last-child {{ border-bottom: none; }}
        </style>
    </head>
    <body>
        <h1>{product.name}</h1>
        <h2>Termékleírás</h2>
        <p>{product.description or "Nincs leírás."}</p>
        
        <h2>Műszaki adatok</h2>
        <div class="specs">{specs_html}</div>

        <h2>Teljes indexelt tartalom (Keresőmotor nézet)</h2>
        <p><small>{product.full_text_content or "Nincs."}</small></p>
    </body>
    </html>
    """
    return html_content


# ==================== TERMÉK ENDPOINTS ====================

@app.get("/products", include_in_schema=False)
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

@app.post("/products", include_in_schema=False)
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
    
    new_product = models.Product(
        name=name,
        description=description,
        price=price,
        category_id=category_id,
        manufacturer_id=manufacturer_id,
        technical_specs=technical_specs
    )
    
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    return new_product.to_dict()


@app.put("/products/{product_id}", response_model=schemas.Product, include_in_schema=False)
def update_product(
    product_id: int,
    product_update: schemas.ProductUpdate,
    db: Session = Depends(get_db)
):
    """
    Egy meglévő termék adatainak frissítése
    
    Args:
        product_id (int): A frissítendő termék ID-ja
        product_update (schemas.ProductUpdate): A frissítendő adatok
                                               Pydantic modellje
        db (Session): Adatbázis session
        
    Returns:
        schemas.Product: A frissített termék adatai
        
    Raises:
        HTTPException: Ha a termék nem található
    """
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    
    if db_product is None:
        raise HTTPException(status_code=404, detail="A termék nem található")
    
    update_data = product_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/health", include_in_schema=False)
async def health_check():
    """Basic health check for monitoring."""
    return {"status": "ok"} 