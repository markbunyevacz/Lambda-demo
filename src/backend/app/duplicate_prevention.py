#!/usr/bin/env python3
"""
Duplicate Prevention System

This module provides tools to prevent duplicate product creation
during database integration processes.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from .models.product import Product
from .models.manufacturer import Manufacturer

logger = logging.getLogger(__name__)


class DuplicatePreventionManager:
    """Prevents duplicate product creation during database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_existing_product(
        self, 
        name: str, 
        manufacturer_id: int,
        source_url: Optional[str] = None,
        sku: Optional[str] = None
    ) -> Optional[Product]:
        """
        Check if a product already exists in the database
        
        Args:
            name: Product name
            manufacturer_id: Manufacturer ID
            source_url: Optional source URL
            sku: Optional SKU
            
        Returns:
            Existing Product if found, None otherwise
        """
        # Build query conditions
        conditions = [
            Product.name == name,
            Product.manufacturer_id == manufacturer_id
        ]
        
        # Add additional unique identifiers if available
        if source_url:
            conditions.append(Product.source_url == source_url)
        
        if sku:
            conditions.append(Product.sku == sku)
        
        # Check for exact match
        existing = self.db.query(Product).filter(*conditions).first()
        
        if existing:
            logger.info(f"Found existing product: {existing.name} (ID: {existing.id})")
            return existing
        
        # Check for similar names (fuzzy matching)
        similar = self.db.query(Product).filter(
            Product.manufacturer_id == manufacturer_id,
            or_(
                Product.name.ilike(f"%{name}%"),
                Product.name.ilike(f"{name}%"),
                Product.name.ilike(f"%{name}")
            )
        ).first()
        
        if similar:
            logger.warning(f"Found similar product: {similar.name} vs {name}")
            return similar
        
        return None
    
    def safe_create_product(self, product_data: Dict[str, Any]) -> Product:
        """
        Safely create a product, checking for duplicates first
        
        Args:
            product_data: Product creation data
            
        Returns:
            Product (existing or newly created)
        """
        # Check for existing product
        existing = self.check_existing_product(
            name=product_data.get('name'),
            manufacturer_id=product_data.get('manufacturer_id'),
            source_url=product_data.get('source_url'),
            sku=product_data.get('sku')
        )
        
        if existing:
            logger.info(f"Returning existing product: {existing.name}")
            return existing
        
        # Create new product
        new_product = Product(**product_data)
        self.db.add(new_product)
        self.db.commit()
        self.db.refresh(new_product)
        
        logger.info(f"Created new product: {new_product.name} (ID: {new_product.id})")
        return new_product
    
    def generate_unique_sku(self, base_name: str, manufacturer_id: int) -> str:
        """Generate a unique SKU for a product"""
        import hashlib
        
        # Create base SKU from name and manufacturer
        base_sku = f"ROCK-{base_name[:10].upper().replace(' ', '')}"
        
        # Check if it already exists
        counter = 1
        sku = base_sku
        
        while self.db.query(Product).filter(Product.sku == sku).first():
            sku = f"{base_sku}-{counter:02d}"
            counter += 1
        
        return sku


def create_database_constraints():
    """Create database-level constraints to prevent duplicates"""
    try:
        from sqlalchemy import text
        from ..database import engine
        
        # Create unique index on (name, manufacturer_id) if not exists
        constraint_sql = """
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'unique_product_name_manufacturer'
            ) THEN
                ALTER TABLE products 
                ADD CONSTRAINT unique_product_name_manufacturer 
                UNIQUE (name, manufacturer_id);
            END IF;
        END $$;
        """
        
        with engine.connect() as conn:
            conn.execute(text(constraint_sql))
            conn.commit()
        
        logger.info("✅ Database constraint created successfully")
        return True
        
    except Exception as e:
        logger.warning(f"⚠️  Database constraint creation failed: {e}")
        return False


def create_source_url_index():
    """Create index on source_url for faster duplicate detection"""
    try:
        from sqlalchemy import text
        from ..database import engine
        
        index_sql = """
        CREATE INDEX IF NOT EXISTS idx_products_source_url 
        ON products (source_url) 
        WHERE source_url IS NOT NULL;
        """
        
        with engine.connect() as conn:
            conn.execute(text(index_sql))
            conn.commit()
        
        logger.info("✅ Source URL index created successfully")
        return True
        
    except Exception as e:
        logger.warning(f"⚠️  Index creation failed: {e}")
        return False 