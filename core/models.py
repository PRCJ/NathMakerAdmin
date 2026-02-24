from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Text, DateTime
from sqlalchemy.orm import relationship
from .database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)


class Catalogue(Base):
    __tablename__ = "catalogue"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    coverImageUrl = Column(String, nullable=True)
    createdAt = Column(DateTime, default=_utcnow)

    products = relationship("Product", back_populates="catalogue", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "product"

    id = Column(Integer, primary_key=True, index=True)
    catalogueId = Column(Integer, ForeignKey("catalogue.id"))
    productName = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    material = Column(String, nullable=True)
    weight = Column(String, nullable=True)
    imageUrls = Column(Text, nullable=True)
    isAvailable = Column(Boolean, default=True)
    createdAt = Column(DateTime, default=_utcnow)

    catalogue = relationship("Catalogue", back_populates="products")
