from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


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


class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: datetime


# AI Service Schemas
class AIChatRequest(BaseModel):
    """Request schema for AI chat endpoint."""
    query: str = Field(..., description="Felhasználó kérdése", min_length=1)
    context_product_ids: Optional[List[int]] = Field(
        default=None, 
        description="Opcionális termék azonosítók kontextushoz"
    )


class AIResponse(BaseModel):
    """Response schema for AI chat endpoint."""
    query: str
    response: str
    context_products: List[Dict[str, Any]] = []
    model_used: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)


class SpecExtractionRequest(BaseModel):
    """Request schema for specification extraction."""
    pdf_content: str = Field(..., description="PDF tartalom szöveges formában")
    product_name: Optional[str] = Field(default=None, description="Termék neve (opcionális)")


class SpecExtractionResponse(BaseModel):
    """Response schema for specification extraction."""
    product_name: Optional[str]
    extracted_specs: Dict[str, Any]
    confidence_score: float = Field(ge=0.0, le=1.0)
    model_used: str


class CompatibilityRequest(BaseModel):
    """Request schema for compatibility analysis."""
    product_ids: List[int] = Field(..., description="Elemzendő termékek azonosítói", min_items=2)


class CompatibilityResponse(BaseModel):
    """Response schema for compatibility analysis."""
    product_ids: List[int]
    compatibility_result: str
    warnings: List[str] = []
    recommendations: List[str] = []
    analysis_details: str
    model_used: str