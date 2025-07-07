#!/usr/bin/env python3
"""
🔧 ADMIN API - PostgreSQL Database Viewer

FastAPI végpontok az adatbázis tartalmának megtekintésére.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from typing import Optional
from datetime import datetime
import logging
import json
from pathlib import Path

from backend.app.database import get_db
from backend.app.models.manufacturer import Manufacturer
from backend.app.models.category import Category
from backend.app.models.product import Product
# ProcessedFileLog is in backend/models/, not app/models/
# from models.processed_file_log import ProcessedFileLog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/test")
async def test_admin_endpoint():
    """
    🧪 Egyszerű teszt endpoint - adatbázis nélkül
    """
    return {
        "success": True, 
        "message": "Admin API működik!", 
        "timestamp": "2025-01-27",
        "endpoints": [
            "/admin/database/overview",
            "/admin/database/products", 
            "/admin/database/manufacturers",
            "/admin/database/categories"
        ]
    }


@router.get("/database/overview")
async def get_database_overview(db: Session = Depends(get_db)):
    """
    📊 Adatbázis áttekintés - gyors statisztikák
    """
    try:
        # Simple count queries first
        try:
            mfr_count = db.execute("SELECT COUNT(*) FROM manufacturers").scalar()
        except Exception:
            mfr_count = 0
            
        try:
            cat_count = db.execute("SELECT COUNT(*) FROM categories").scalar()
        except Exception:
            cat_count = 0
            
        try:
            prod_count = db.execute("SELECT COUNT(*) FROM products").scalar()
        except Exception:
            prod_count = 0
        
        stats = {
            "manufacturers": mfr_count,
            "categories": cat_count, 
            "products": prod_count,
            "processed_files": 0,  # Temporarily disabled: ProcessedFileLog
            "last_updated": datetime.now().isoformat(),
            "database_status": "connected"
        }
        
        # Gyártók szerinti termékszámok
        manufacturer_stats = (
            db.query(
                Manufacturer.name,
                func.count(Product.id).label('product_count')
            )
            .outerjoin(Product)
            .group_by(Manufacturer.id, Manufacturer.name)
            .all()
        )
        
        stats["products_by_manufacturer"] = [
            {"manufacturer": name, "count": count}
            for name, count in manufacturer_stats
        ]
        
        return {"success": True, "data": stats}
        
    except Exception as e:
        # UTF-8 safe error handling
        error_msg = str(e).encode('utf-8', errors='ignore').decode('utf-8')
        logger.error(f"Database overview failed: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/database/products")
async def get_products(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    manufacturer: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    📋 Termékek listázása szűrési lehetőségekkel
    """
    try:
        query = (
            db.query(Product)
            .options(
                joinedload(Product.manufacturer),
                joinedload(Product.category)
            )
        )
        
        # Szűrések
        if manufacturer:
            query = query.join(Manufacturer).filter(
                Manufacturer.name.ilike(f"%{manufacturer}%")
            )
        
        if category:
            query = query.join(Category).filter(
                Category.name.ilike(f"%{category}%")
            )
        
        # Rendezés és lapozás
        total = query.count()
        products = (
            query.order_by(desc(Product.id))
            .offset(offset)
            .limit(limit)
            .all()
        )
        
        # Formázás
        product_list = []
        for product in products:
            product_data = {
                "id": product.id,
                "name": product.name,
                "sku": product.sku,
                "price": product.price,
                "manufacturer": product.manufacturer.name if product.manufacturer else None,
                "category": product.category.name if product.category else None,
                "technical_specs_count": len(product.technical_specs) if product.technical_specs else 0,
                "has_full_text": bool(product.full_text_content),
                "full_text_length": len(product.full_text_content) if product.full_text_content else 0,
                "created_at": product.created_at.isoformat() if hasattr(product, 'created_at') and product.created_at else None
            }
            product_list.append(product_data)
        
        return {
            "success": True,
            "data": {
                "products": product_list,
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Products listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/product/{product_id}")
async def get_product_detail(product_id: int, db: Session = Depends(get_db)):
    """
    🔍 Termék részletes adatai
    """
    try:
        product = (
            db.query(Product)
            .options(
                joinedload(Product.manufacturer),
                joinedload(Product.category)
            )
            .filter(Product.id == product_id)
            .first()
        )
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Teljes adat formázás
        product_detail = {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "sku": product.sku,
            "price": product.price,
            "manufacturer": {
                "id": product.manufacturer.id,
                "name": product.manufacturer.name,
                "website": product.manufacturer.website
            } if product.manufacturer else None,
            "category": {
                "id": product.category.id,
                "name": product.category.name,
                "parent_id": product.category.parent_id
            } if product.category else None,
            "technical_specs": product.technical_specs,
            "full_text_content": product.full_text_content,
            "full_text_length": len(product.full_text_content) if product.full_text_content else 0,
            "created_at": product.created_at.isoformat() if hasattr(product, 'created_at') and product.created_at else None
        }
        
        return {"success": True, "data": product_detail}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Product detail failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# @router.get("/database/processed-files")
# async def get_processed_files(
#     limit: int = Query(50, ge=1, le=200),
#     offset: int = Query(0, ge=0),
#     db: Session = Depends(get_db)
# ):
#     """
#     📁 Feldolgozott fájlok listája - TEMPORARILY DISABLED
#     """
#     # Temporarily disabled due to missing ProcessedFileLog import
#     return {"success": False, "message": "ProcessedFileLog not available"}


@router.get("/database/manufacturers")
async def get_manufacturers(db: Session = Depends(get_db)):
    """
    🏭 Gyártók listája termékszámokkal
    """
    try:
        manufacturers = (
            db.query(
                Manufacturer.id,
                Manufacturer.name,
                Manufacturer.website,
                func.count(Product.id).label('product_count')
            )
            .outerjoin(Product)
            .group_by(Manufacturer.id, Manufacturer.name, Manufacturer.website)
            .order_by(desc('product_count'))
            .all()
        )
        
        manufacturer_list = []
        for mfr in manufacturers:
            manufacturer_data = {
                "id": mfr.id,
                "name": mfr.name,
                "website": mfr.website,
                "product_count": mfr.product_count
            }
            manufacturer_list.append(manufacturer_data)
        
        return {"success": True, "data": manufacturer_list}
        
    except Exception as e:
        logger.error(f"Manufacturers listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/categories")
async def get_categories(db: Session = Depends(get_db)):
    """
    📂 Kategóriák listája termékszámokkal
    """
    try:
        categories = (
            db.query(
                Category.id,
                Category.name,
                Category.parent_id,
                func.count(Product.id).label('product_count')
            )
            .outerjoin(Product)
            .group_by(Category.id, Category.name, Category.parent_id)
            .order_by(desc('product_count'))
            .all()
        )
        
        category_list = []
        for cat in categories:
            category_data = {
                "id": cat.id,
                "name": cat.name,
                "parent_id": cat.parent_id,
                "product_count": cat.product_count
            }
            category_list.append(category_data)
        
        return {"success": True, "data": category_list}
        
    except Exception as e:
        logger.error(f"Categories listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/search")
async def search_products(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    🔍 Termék keresés név és leírás alapján
    """
    try:
        search_term = f"%{q}%"
        
        products = (
            db.query(Product)
            .options(
                joinedload(Product.manufacturer),
                joinedload(Product.category)
            )
            .filter(
                (Product.name.ilike(search_term)) |
                (Product.description.ilike(search_term)) |
                (Product.sku.ilike(search_term))
            )
            .limit(limit)
            .all()
        )
        
        search_results = []
        for product in products:
            result = {
                "id": product.id,
                "name": product.name,
                "sku": product.sku,
                "manufacturer": product.manufacturer.name if product.manufacturer else None,
                "category": product.category.name if product.category else None
            }
            search_results.append(result)
        
        return {
            "success": True,
            "data": {
                "query": q,
                "results": search_results,
                "count": len(search_results)
            }
        }
        
    except Exception as e:
        logger.error(f"Product search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 


@router.get("/analysis/extraction-comparison")
async def get_extraction_comparison_report():
    """
    📊 PDF adatkinyerés elemzési riport.
    """
    # Structured extraction results - try multiple possible locations
    import os
    
    possible_paths = [
        Path("real_pdf_extraction_results.json"),  # Same directory as API
        Path("src/backend/real_pdf_extraction_results.json"),  # From project root
        Path("../real_pdf_extraction_results.json"),  # One level up
        Path("../../real_pdf_extraction_results.json"),  # Two levels up
        Path(os.getcwd()) / "src" / "backend" / "real_pdf_extraction_results.json"  # Absolute
    ]
    
    report_path = None
    for path in possible_paths:
        if path.exists():
            report_path = path
            break
    
    if not report_path:
        raise HTTPException(status_code=404, detail="Extraction results not found. Please run the PDF processor first.")
    
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            extraction_data = json.load(f)
        
        # Convert to frontend format
        comparison_data = []
        for result in extraction_data.get("results", []):
            comparison_entry = {
                "pdf_filename": result.get("source_filename", ""),
                "structured_extraction": result
            }
            comparison_data.append(comparison_entry)
        
        return {"success": True, "data": comparison_data}
    except Exception as e:
        logger.error(f"Failed to read or parse extraction results: {e}")
        raise HTTPException(status_code=500, detail="Failed to process extraction results.") 