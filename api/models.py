from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)


class Catalogue(Base):
    __tablename__ = "catalogue"

    id = Column(Integer, primary_key=True, index=True)
    catalogue_name = Column(String, nullable=False)
    items = relationship("Item", back_populates="catalogue", cascade="all, delete-orphan")


class Item(Base):
    __tablename__ = "item"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    type = Column(String, nullable=False)
    catalogue_id = Column(Integer, ForeignKey("catalogue.id"))
    catalogue = relationship("Catalogue", back_populates="items")


class Product(Base):
    __tablename__ = "product"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
