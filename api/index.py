import os
from typing import Optional

import models
import database
from database import engine, get_db

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Create DB tables on startup (equivalent to ddl-auto=update)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="NathMaker Admin API")

# ─── CORS ────────────────────────────────────────────────────────────────────
frontend_url = os.environ.get("FRONTEND_URL", "https://your-app.vercel.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Pydantic Schemas ─────────────────────────────────────────────────────────
class ItemSchema(BaseModel):
    id: Optional[int] = None
    code: str
    price: float
    type: str

    class Config:
        from_attributes = True


class CatalogueSchema(BaseModel):
    id: Optional[int] = None
    catalogue_name: str
    items: list[ItemSchema] = []

    class Config:
        from_attributes = True


class ProductSchema(BaseModel):
    id: Optional[int] = None
    name: str
    price: float

    class Config:
        from_attributes = True


class AdminSchema(BaseModel):
    id: Optional[int] = None
    name: str

    class Config:
        from_attributes = True


# ─── Admin Endpoints ──────────────────────────────────────────────────────────
@app.get("/admin/hello")
def hello():
    return "Hello from NathMaker FastAPI!"


@app.get("/admin/", response_model=list[AdminSchema])
def get_all_admins(db: Session = Depends(get_db)):
    return db.query(models.Admin).all()


@app.post("/admin/", response_model=AdminSchema, status_code=201)
def create_admin(admin: AdminSchema, db: Session = Depends(get_db)):
    db_admin = models.Admin(name=admin.name)
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin


# ─── Catalogue Endpoints ──────────────────────────────────────────────────────
@app.get("/api/catalogue", response_model=list[CatalogueSchema])
def get_all_catalogues(db: Session = Depends(get_db)):
    return db.query(models.Catalogue).all()


@app.post("/api/catalogue", response_model=CatalogueSchema, status_code=201)
def create_catalogue(catalogue: CatalogueSchema, db: Session = Depends(get_db)):
    db_catalogue = models.Catalogue(catalogue_name=catalogue.catalogue_name)
    db_catalogue.items = [
        models.Item(code=item.code, price=item.price, type=item.type)
        for item in catalogue.items
    ]
    db.add(db_catalogue)
    db.commit()
    db.refresh(db_catalogue)
    return db_catalogue


# ─── Product Endpoints ────────────────────────────────────────────────────────
@app.get("/products", response_model=list[ProductSchema])
def get_all_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()


@app.get("/products/{product_id}", response_model=ProductSchema)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/products", response_model=ProductSchema, status_code=201)
def create_product(product: ProductSchema, db: Session = Depends(get_db)):
    db_product = models.Product(name=product.name, price=product.price)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.put("/products/{product_id}", response_model=ProductSchema)
def update_product(product_id: int, updated: ProductSchema, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.name = updated.name
    product.price = updated.price
    db.commit()
    db.refresh(product)
    return product


@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}
