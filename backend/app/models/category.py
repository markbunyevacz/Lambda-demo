from __future__ import annotations

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    parent_id = Column(Integer, ForeignKey('categories.id'))

    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent")
    products = relationship("Product", back_populates="category")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "children": [child.to_dict() for child in self.children]
        } 