from __future__ import annotations

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from ..database import Base


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    level = Column(Integer, default=0, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent")
    products = relationship("Product", back_populates="category")

    def to_dict(self, include_children: bool = False, include_parent: bool = False) -> dict:
        """Konvertálja a modellt szótárrá."""
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parent_id": self.parent_id,
            "level": self.level,
            "sort_order": self.sort_order,
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_parent and self.parent:
            result["parent"] = self.parent.to_dict()
            
        if include_children and self.children:
            result["children"] = [child.to_dict() for child in self.children]
            
        return result

    def get_full_path(self) -> str:
        """Visszaadja a kategória teljes hierarchikus útvonalát."""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', level={self.level})>" 