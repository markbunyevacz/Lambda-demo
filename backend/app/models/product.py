from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    price = Column(Float)
    price_unit = Column(String)  # e.g., 'HUF/m2', 'HUF/db'

    manufacturer_id = Column(Integer, ForeignKey('manufacturers.id'))
    category_id = Column(Integer, ForeignKey('categories.id'))

    technical_specifications = Column(JSONB)
    image_urls = Column(JSONB)
    document_urls = Column(JSONB)

    manufacturer = relationship("Manufacturer", back_populates="products")
    category = relationship("Category", back_populates="products")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "price_unit": self.price_unit,
            "technical_specifications": self.technical_specifications,
            "image_urls": self.image_urls,
            "document_urls": self.document_urls,
            "manufacturer": self.manufacturer.to_dict() if self.manufacturer else None,
            "category": self.category.to_dict() if self.category else None,
        } 