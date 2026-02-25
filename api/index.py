import os
import sys
import json
import hashlib
from datetime import datetime
from typing import Optional, List

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File, Form, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

import cloudinary
import cloudinary.uploader

from core import models
from core.database import Base, get_engine, get_db

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    try:
        Base.metadata.create_all(bind=get_engine())
    except Exception:
        pass
    yield

app = FastAPI(title="NathMaker API", lifespan=lifespan)

frontend_url = os.environ.get("FRONTEND_URL", "https://nath-maker-admin-sigma.vercel.app")

allowed_origins = [frontend_url, "http://localhost:8081"]
if os.environ.get("ALLOW_ALL_ORIGINS"):
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', 'demo'),
    api_key=os.environ.get('CLOUDINARY_API_KEY', 'default_key'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET', 'default_secret')
)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _parse_image_urls(product):
    """Parse imageUrls from JSON string to list in-place."""
    if isinstance(product.imageUrls, str):
        try:
            product.imageUrls = json.loads(product.imageUrls)
        except (json.JSONDecodeError, TypeError):
            product.imageUrls = []
    elif product.imageUrls is None:
        product.imageUrls = []


# ─── Schemas ──────────────────────────────────────────────────────────────────

class CatalogueCreate(BaseModel):
    name: str
    description: Optional[str] = None
    coverImageUrl: Optional[str] = None

class CatalogueSchema(CatalogueCreate):
    id: int
    createdAt: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class ProductCreate(BaseModel):
    catalogueId: int
    productName: str
    description: Optional[str] = None
    price: float
    material: Optional[str] = None
    weight: Optional[str] = None
    imageUrls: Optional[List[str]] = []
    isAvailable: bool = True

class ProductSchema(ProductCreate):
    id: int
    createdAt: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ─── API Endpoints ────────────────────────────────────────────────────────────
api_router = APIRouter(prefix="/api")

_tables_created = False

def ensure_tables():
    global _tables_created
    if not _tables_created:
        try:
            Base.metadata.create_all(bind=get_engine())
            _tables_created = True
        except Exception:
            pass

@api_router.get("/catalogues", response_model=List[CatalogueSchema])
def get_all_catalogues(db: Session = Depends(get_db)):
    ensure_tables()
    return db.query(models.Catalogue).all()

@api_router.post("/catalogues", response_model=CatalogueSchema, status_code=201)
def create_catalogue(cat: CatalogueCreate, db: Session = Depends(get_db)):
    db_cat = models.Catalogue(
        name=cat.name,
        description=cat.description,
        coverImageUrl=cat.coverImageUrl
    )
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat

@api_router.get("/products", response_model=List[ProductSchema])
def get_products(catalogueId: Optional[int] = None, db: Session = Depends(get_db)):
    ensure_tables()
    query = db.query(models.Product)
    if catalogueId:
        query = query.filter(models.Product.catalogueId == catalogueId)
    products = query.all()
    for p in products:
        _parse_image_urls(p)
    return products

@api_router.get("/products/{product_id}", response_model=ProductSchema)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    _parse_image_urls(product)
    return product

@api_router.post("/products", response_model=ProductSchema, status_code=201)
def create_product(prod: ProductCreate, db: Session = Depends(get_db)):
    db_prod = models.Product(
        catalogueId=prod.catalogueId,
        productName=prod.productName,
        description=prod.description,
        price=prod.price,
        material=prod.material,
        weight=prod.weight,
        imageUrls=json.dumps(prod.imageUrls or []),
        isAvailable=prod.isAvailable
    )
    db.add(db_prod)
    db.commit()
    db.refresh(db_prod)
    _parse_image_urls(db_prod)
    return db_prod

@api_router.put("/products/{product_id}", response_model=ProductSchema)
def update_product(product_id: int, updated: ProductCreate, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.catalogueId = updated.catalogueId
    product.productName = updated.productName
    product.description = updated.description
    product.price = updated.price
    product.material = updated.material
    product.weight = updated.weight
    product.imageUrls = json.dumps(updated.imageUrls or [])
    product.isAvailable = updated.isAvailable

    db.commit()
    db.refresh(product)
    _parse_image_urls(product)
    return product

@api_router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}

@api_router.post("/upload")
def upload_image(file: UploadFile = File(...)):
    try:
        result = cloudinary.uploader.upload(file.file)
        return {"imageUrl": result.get("secure_url")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(api_router)

# ─── Admin Endpoints ──────────────────────────────────────────────────────────

ADMIN_PASS = os.environ.get("ADMIN_PASSWORD", "admin123")
_admin_token = hashlib.sha256(ADMIN_PASS.encode()).hexdigest()

def enforce_admin(request: Request):
    if request.cookies.get("admin_token") != _admin_token:
        raise HTTPException(status_code=302, headers={"Location": "/admin/login"})

@app.get("/admin/init-db")
def init_db():
    try:
        Base.metadata.create_all(bind=get_engine())
        return {"message": "Database tables created successfully"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/admin", response_class=RedirectResponse)
def admin_redirect():
    return RedirectResponse(url="/admin/dashboard")

@app.get("/admin/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/admin/login")
def login_submit(request: Request, password: str = Form(...)):
    if password == ADMIN_PASS:
        response = RedirectResponse(url="/admin/dashboard", status_code=302)
        response.set_cookie(key="admin_token", value=_admin_token, httponly=True, samesite="lax")
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid password"})

@app.get("/admin/logout")
def logout():
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("admin_token")
    return response

@app.get("/admin/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    enforce_admin(request)
    total_products = db.query(models.Product).count()
    total_catalogues = db.query(models.Catalogue).count()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total_products": total_products,
        "total_catalogues": total_catalogues
    })

@app.get("/admin/catalogues", response_class=HTMLResponse)
def admin_catalogues(request: Request, db: Session = Depends(get_db)):
    enforce_admin(request)
    catalogues = db.query(models.Catalogue).all()
    return templates.TemplateResponse("catalogues.html", {
        "request": request,
        "catalogues": catalogues
    })

@app.post("/admin/catalogues/add")
def add_catalogue(request: Request, name: str = Form(...), description: str = Form(""), coverImageUrl: str = Form(""), db: Session = Depends(get_db)):
    enforce_admin(request)
    cat = models.Catalogue(name=name, description=description, coverImageUrl=coverImageUrl)
    db.add(cat)
    db.commit()
    return RedirectResponse(url="/admin/catalogues", status_code=302)

@app.post("/admin/catalogues/delete/{id}")
def delete_catalogue(request: Request, id: int, db: Session = Depends(get_db)):
    enforce_admin(request)
    cat = db.query(models.Catalogue).filter(models.Catalogue.id == id).first()
    if cat:
        db.delete(cat)
        db.commit()
    return RedirectResponse(url="/admin/catalogues", status_code=302)

@app.get("/admin/products", response_class=HTMLResponse)
def admin_products(request: Request, db: Session = Depends(get_db)):
    enforce_admin(request)
    products = db.query(models.Product).all()
    for p in products:
        _parse_image_urls(p)

    catalogues = {c.id: c.name for c in db.query(models.Catalogue).all()}

    return templates.TemplateResponse("products.html", {
        "request": request,
        "products": products,
        "catalogues": catalogues
    })

@app.get("/admin/product/add", response_class=HTMLResponse)
def admin_product_add_form(request: Request, db: Session = Depends(get_db)):
    enforce_admin(request)
    catalogues = db.query(models.Catalogue).all()
    return templates.TemplateResponse("product_form.html", {
        "request": request,
        "catalogues": catalogues,
        "product": None
    })

@app.get("/admin/product/edit/{id}", response_class=HTMLResponse)
def admin_product_edit_form(request: Request, id: int, db: Session = Depends(get_db)):
    enforce_admin(request)
    product = db.query(models.Product).filter(models.Product.id == id).first()
    if product:
        _parse_image_urls(product)
    catalogues = db.query(models.Catalogue).all()
    return templates.TemplateResponse("product_form.html", {
        "request": request,
        "catalogues": catalogues,
        "product": product
    })

@app.post("/admin/product/save")
def admin_product_save(
    request: Request,
    id: Optional[int] = Form(None),
    catalogueId: int = Form(...),
    productName: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    material: str = Form(""),
    weight: str = Form(""),
    isAvailable: bool = Form(True),
    imageUrls: str = Form("[]"),
    db: Session = Depends(get_db)
):
    enforce_admin(request)
    if id:
        product = db.query(models.Product).filter(models.Product.id == id).first()
        product.catalogueId = catalogueId
        product.productName = productName
        product.description = description
        product.price = price
        product.material = material
        product.weight = weight
        product.isAvailable = isAvailable
        product.imageUrls = imageUrls
    else:
        product = models.Product(
            catalogueId=catalogueId,
            productName=productName,
            description=description,
            price=price,
            material=material,
            weight=weight,
            isAvailable=isAvailable,
            imageUrls=imageUrls
        )
        db.add(product)
    
    db.commit()
    return RedirectResponse(url="/admin/products", status_code=302)

@app.post("/admin/product/delete/{id}")
def admin_product_delete(request: Request, id: int, db: Session = Depends(get_db)):
    enforce_admin(request)
    product = db.query(models.Product).filter(models.Product.id == id).first()
    if product:
        db.delete(product)
        db.commit()
    return RedirectResponse(url="/admin/products", status_code=302)


# ─── Local dev: serve frontend static files ──────────────────────────────────

PUBLIC_DIR = os.path.join(BASE_DIR, "..", "public")

if os.path.isdir(PUBLIC_DIR):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    @app.get("/", response_class=HTMLResponse)
    def serve_index():
        return FileResponse(os.path.join(PUBLIC_DIR, "index.html"))

    app.mount("/", StaticFiles(directory=PUBLIC_DIR, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.index:app", host="0.0.0.0", port=8081, reload=True)

