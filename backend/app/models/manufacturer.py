from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Manufacturer(Base):
    __tablename__ = 'manufacturers'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True, nullable=False)
    website_url = Column(String)

    products = relationship("Product", back_populates="manufacturer")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "website_url": self.website_url,
        } 