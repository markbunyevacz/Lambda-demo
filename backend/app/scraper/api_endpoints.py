"""
Scraper API Endpoints - FastAPI végpontok a Rockwool scraper kezelésére

Ez a modul tartalmazza a scraper funkcionalitást elérhetővé tevő
REST API végpontokat a Lambda.hu alkalmazásban.
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel

from .rockwool_scraper import RockwoolScraper, ScrapingConfig
from .data_validator import DataValidator

logger = logging.getLogger(__name__)

# Router létrehozása
scraper_router = APIRouter(
    prefix="/api/scraper",
    tags=["Scraper"]
)

# Globális scraper példány
scraper_instance: Optional[RockwoolScraper] = None
scraper_running = False


class ScrapingRequest(BaseModel):
    """Scraping kérés modellje"""
    max_products_per_category: Optional[int] = 10
    max_categories: Optional[int] = None
    test_mode: bool = False
    specific_urls: Optional[List[str]] = None


class ScrapingStatus(BaseModel):
    """Scraping állapot modellje"""
    is_running: bool
    scraped_urls: int
    failed_urls: int
    last_activity: Optional[datetime]
    error_message: Optional[str] = None


class ProductSummary(BaseModel):
    """Termék összefoglaló modellje"""
    name: str
    url: str
    category: str
    description_length: int
    technical_specs_count: int
    images_count: int
    documents_count: int


class ScrapingResult(BaseModel):
    """Scraping eredmény modellje"""
    success: bool
    total_products: int
    valid_products: int
    invalid_products: int
    categories_processed: int
    duration_seconds: float
    validation_report: Dict
    sample_products: List[ProductSummary]


def get_scraper() -> RockwoolScraper:
    """Scraper példány lekérése"""
    global scraper_instance
    if scraper_instance is None:
        config = ScrapingConfig()
        scraper_instance = RockwoolScraper(config)
    return scraper_instance


@scraper_router.get("/status", response_model=ScrapingStatus)
async def get_scraping_status():
    """
    Scraping állapot lekérése
    
    Returns:
        ScrapingStatus: Aktuális scraping állapot
    """
    global scraper_running
    
    scraper = get_scraper()
    stats = scraper.get_scraping_statistics()
    
    return ScrapingStatus(
        is_running=scraper_running,
        scraped_urls=stats['scraped_urls'],
        failed_urls=stats['failed_urls'],
        last_activity=datetime.now() if scraper_running else None
    )


@scraper_router.get("/website-structure")
async def discover_website_structure():
    """
    Rockwool weboldal struktúrájának feltérképezése
    
    Returns:
        Dict: Weboldal struktúra (kategóriák, termék oldalak)
    """
    try:
        scraper = get_scraper()
        structure = scraper.discover_website_structure()
        
        return {
            "success": True,
            "structure": structure,
            "discovered_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Hiba a weboldal struktúra feltérképezésében: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Weboldal struktúra feltérképezése sikertelen: {str(e)}"
        )


@scraper_router.post("/scrape/single-product")
async def scrape_single_product(product_url: str):
    """
    Egyetlen termék scraping-je
    
    Args:
        product_url: Scraping-elni kívánt termék URL-je
        
    Returns:
        Dict: Scraped termék adatok
    """
    try:
        scraper = get_scraper()
        validator = DataValidator()
        
        logger.info(f"Egyetlen termék scraping: {product_url}")
        product = scraper._scrape_single_product(product_url)
        
        if not product:
            raise HTTPException(
                status_code=404,
                detail="Termék scraping sikertelen vagy nem található"
            )
        
        # Validálás
        is_valid = validator.validate_product(product)
        
        return {
            "success": True,
            "product": {
                "name": product.name,
                "url": product.url,
                "category": product.category,
                "description": product.description,
                "technical_specs": product.technical_specs,
                "images": product.images,
                "documents": product.documents,
                "price": product.price,
                "availability": product.availability,
                "scraped_at": product.scraped_at.isoformat() if product.scraped_at else None
            },
            "validation": {
                "is_valid": is_valid,
                "validator_used": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hiba az egyetlen termék scraping során: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Termék scraping hiba: {str(e)}"
        )


@scraper_router.post("/scrape/start", response_model=Dict)
async def start_scraping(
    request: ScrapingRequest,
    background_tasks: BackgroundTasks
):
    """
    Teljes Rockwool scraping indítása háttérben
    
    Args:
        request: Scraping kérés paraméterei
        background_tasks: FastAPI háttér feladatok
        
    Returns:
        Dict: Scraping indítási válasz
    """
    global scraper_running
    
    if scraper_running:
        raise HTTPException(
            status_code=409,
            detail="Scraping már folyamatban van"
        )
    
    try:
        # Háttér scraping indítása
        background_tasks.add_task(
            run_full_scraping,
            request.max_products_per_category,
            request.max_categories,
            request.test_mode,
            request.specific_urls
        )
        
        scraper_running = True
        
        return {
            "success": True,
            "message": "Scraping elindítva háttérben",
            "parameters": request.dict(),
            "started_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Hiba a scraping indításában: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Scraping indítás sikertelen: {str(e)}"
        )


@scraper_router.post("/scrape/stop")
async def stop_scraping():
    """
    Folyamatban lévő scraping leállítása
    
    Returns:
        Dict: Leállítási eredmény
    """
    global scraper_running
    
    if not scraper_running:
        raise HTTPException(
            status_code=400,
            detail="Nincs folyamatban scraping"
        )
    
    # Egyszerű megállítás jelzés (fejlettebb implementációhoz szükség lenne task management-re)
    scraper_running = False
    
    return {
        "success": True,
        "message": "Scraping leállítva",
        "stopped_at": datetime.now().isoformat()
    }


@scraper_router.get("/results/validation-report")
async def get_last_validation_report():
    """
    Legutolsó validálási jelentés lekérése
    
    Returns:
        Dict: Validálási jelentés
    """
    # TODO: Implementálni az eredmények mentését és lekérését
    # Egyelőre placeholder válasz
    return {
        "success": True,
        "message": "Validálási jelentés funkció fejlesztés alatt",
        "available_soon": True
    }


@scraper_router.get("/health")
async def scraper_health_check():
    """
    Scraper egészségügyi ellenőrzés
    
    Returns:
        Dict: Scraper állapot és konfiguráció
    """
    try:
        scraper = get_scraper()
        
        # Egyszerű kapcsolat teszt
        test_url = "https://www.rockwool.hu"
        import requests
        response = requests.get(test_url, timeout=10)
        connection_ok = response.status_code == 200
        
        return {
            "scraper_ready": True,
            "rockwool_connection": connection_ok,
            "configuration": {
                "base_url": scraper.config.base_url,
                "request_delay": scraper.config.request_delay,
                "max_retries": scraper.config.max_retries
            },
            "statistics": scraper.get_scraping_statistics(),
            "checked_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Scraper egészségügyi ellenőrzés hiba: {e}")
        return {
            "scraper_ready": False,
            "error": str(e),
            "checked_at": datetime.now().isoformat()
        }


async def run_full_scraping(
    max_products_per_category: Optional[int] = None,
    max_categories: Optional[int] = None,
    test_mode: bool = False,
    specific_urls: Optional[List[str]] = None
):
    """
    Teljes scraping futtatása háttérben
    
    Args:
        max_products_per_category: Max termékek kategóriánként
        max_categories: Max kategóriák
        test_mode: Teszt mód (korlátozott scraping)
        specific_urls: Specifikus URL-ek listája
    """
    global scraper_running
    
    start_time = datetime.now()
    
    try:
        logger.info("Teljes Rockwool scraping elindítva")
        
        scraper = get_scraper()
        validator = DataValidator()
        
        if specific_urls:
            # Specifikus URL-ek scraping-je
            products = []
            for url in specific_urls:
                product = scraper._scrape_single_product(url)
                if product:
                    products.append(product)
        else:
            # Teljes weboldal scraping (korlátozott)
            if test_mode:
                max_products_per_category = min(max_products_per_category or 2, 2)
                max_categories = min(max_categories or 2, 2)
            
            # Weboldal struktúra feltérképezése
            structure = scraper.discover_website_structure()
            
            products = []
            categories_processed = 0
            
            # Kategóriák feldolgozása
            for category_url in structure['categories']:
                if max_categories and categories_processed >= max_categories:
                    break
                
                logger.info(f"Kategória feldolgozása: {category_url}")
                category_products = scraper._scrape_category_products(category_url)
                
                # Limitálás
                if max_products_per_category:
                    category_products = category_products[:max_products_per_category]
                
                products.extend(category_products)
                categories_processed += 1
        
        # Validálás
        validation_report = validator.get_validation_report(products)
        
        # Eredmények mentése (TODO: adatbázisba)
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Scraping befejezve: {len(products)} termék, {duration:.1f} másodperc")
        logger.info(f"Validálási eredmény: {validation_report['summary']}")
        
    except Exception as e:
        logger.error(f"Hiba a háttér scraping során: {e}")
    finally:
        scraper_running = False 