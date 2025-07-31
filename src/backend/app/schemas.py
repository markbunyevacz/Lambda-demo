from pydantic import BaseModel
from typing import Optional, List


class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10


class SearchResult(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    score: Optional[float] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_count: int


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None


class Product(ProductBase):
    id: int
    
    class Config:
        from_attributes = True