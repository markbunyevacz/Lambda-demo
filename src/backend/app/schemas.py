from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- Manufacturer Schemas ---
class ManufacturerBase(BaseModel):
    name: str
    description: Optional[str] = None
    website: Optional[str] = None
    country: Optional[str] = None

class ManufacturerCreate(ManufacturerBase):
    pass

class Manufacturer(ManufacturerBase):
    id: int

    class Config:
        from_attributes = True

# --- Category Schemas ---
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    children: List['Category'] = []

    class Config:
        from_attributes = True

# --- Product Schemas (Now defined AFTER Manufacturer and Category) ---
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    technical_specs: Optional[dict] = None
    raw_specs: Optional[dict] = None
    full_text_content: Optional[str] = None
    category_id: Optional[int] = None
    manufacturer_id: Optional[int] = None

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    manufacturer: Optional[Manufacturer] = None
    category: Optional[Category] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    technical_specs: Optional[dict] = None
    raw_specs: Optional[dict] = None
    full_text_content: Optional[str] = None
    category_id: Optional[int] = None

# This line tells Pydantic to resolve the forward reference for 'Category' in Category.children
Category.model_rebuild()

class ScrapeRequest(BaseModel):
    scraper_type: str 

class SearchRequest(BaseModel):
    query: str
    limit: int = 10 