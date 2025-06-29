from pydantic import BaseModel
from typing import List, Optional


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    # ... Add other product fields as needed


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: int
    category_id: int
    manufacturer_id: int

    class Config:
        orm_mode = True


class Category(BaseModel):
    id: int
    name: str
    products: List[Product] = []

    class Config:
        orm_mode = True


class ScrapeRequest(BaseModel):
    scraper_type: str 