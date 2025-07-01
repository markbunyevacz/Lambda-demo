from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    # ... Add other product fields as needed


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


class Category(BaseModel):
    id: int
    name: str
    products: List[Product] = []

    class Config:
        orm_mode = True


class ScrapeRequest(BaseModel):
    scraper_type: str


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    technical_specs: Optional[dict] = None
    raw_specs: Optional[dict] = None
    full_text_content: Optional[str] = None
    category_id: Optional[int] = None


class CategoryBase(BaseModel):
    name: str 