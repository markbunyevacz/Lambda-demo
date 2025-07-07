from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func, Numeric, Boolean, JSON
from sqlalchemy.orm import relationship
from ..database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(512), nullable=False, index=True)
    description = Column(Text, nullable=True)
    full_text_content = Column(Text, nullable=True)
    sku = Column(String(100), nullable=True, unique=True, index=True)
    
    # Külső kulcsok
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    
    # Ár és egység információk
    price = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), default="HUF", nullable=False)
    unit = Column(String(50), nullable=True)  # m2, db, m3, stb.
    
    # Műszaki paraméterek és metaadatok
    technical_specs = Column(JSON, nullable=True)  # Normalizált műszaki adatok
    raw_specs = Column(JSON, nullable=True)       # Eredeti scraped adatok
    images = Column(JSON, nullable=True)          # Képek URL-jei
    documents = Column(JSON, nullable=True)       # Műszaki dokumentumok
    
    # Scraping és státusz információk
    source_url = Column(String(1024), nullable=True)
    scraped_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    in_stock = Column(Boolean, default=True, nullable=False)
    
    # Időbélyegek
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Kapcsolatok
    manufacturer = relationship("Manufacturer", back_populates="products")
    category = relationship("Category", back_populates="products")

    def to_dict(self, include_relations: bool = True) -> dict:
        """Konvertálja a modellt szótárrá."""
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "full_text_content": self.full_text_content,
            "sku": self.sku,
            "manufacturer_id": self.manufacturer_id,
            "category_id": self.category_id,
            "price": float(self.price) if self.price else None,
            "currency": self.currency,
            "unit": self.unit,
            "technical_specs": self.technical_specs,
            "raw_specs": self.raw_specs,
            "images": self.images,
            "documents": self.documents,
            "source_url": self.source_url,
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
            "is_active": self.is_active,
            "in_stock": self.in_stock,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_relations:
            if self.manufacturer:
                result["manufacturer"] = self.manufacturer.to_dict()
            if self.category:
                result["category"] = self.category.to_dict()
                
        return result

    def get_display_price(self) -> str:
        """Visszaadja a formázott árat."""
        if self.price:
            return f"{self.price:,.0f} {self.currency}"
        return "Ár egyeztetés szerint"

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', sku='{self.sku}')>" 