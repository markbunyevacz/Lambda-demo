from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class Manufacturer(Base):
    __tablename__ = 'manufacturers'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    website = Column(String(512), nullable=True)
    country = Column(String(100), nullable=True)
    logo_url = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    products = relationship("Product", back_populates="manufacturer")

    def to_dict(self) -> dict:
        """Konvertálja a modellt szótárrá."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "website": self.website,
            "country": self.country,
            "logo_url": self.logo_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Manufacturer(id={self.id}, name='{self.name}')>" 