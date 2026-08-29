import os
import sys
import json
import hashlib
import time
from datetime import datetime
from typing import Optional, List

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File, Form, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.orm import Session

from core import models
from core.database import Base, get_engine, get_db
from core.excel_import import parse_spreadsheet, build_template_xlsx
from core.blob_store import (
    ALLOWED_IMAGE_TYPES,
    MAX_IMAGE_BYTES,
    blob_configured,
    blob_status,
    normalize_image_type,
    upload_image_bytes,
)

from contextlib import asynccontextmanager

_ENABLE_DOCS = os.environ.get("ENABLE_DOCS") == "1"
_IS_PRODUCTION = os.environ.get("VERCEL_ENV") == "production"

LOGIN_WINDOW_SECONDS = 15 * 60
LOGIN_MAX_FAILURES = 5
_login_failures = {}


def _admin_password() -> str:
    pw = (os.environ.get("ADMIN_PASSWORD") or "").strip()
    if not pw:
        raise RuntimeError("ADMIN_PASSWORD is required")
    return pw


def _admin_cookie_value() -> str:
    return hashlib.sha256(_admin_password().encode()).hexdigest()


def _cookie_secure() -> bool:
    return _IS_PRODUCTION


def _cors_origins():
    origins = [
        "https://nathmakers.com",
        "https://www.nathmakers.com",
        "https://nath-maker-admin-sigma.vercel.app",
    ]
    extra = os.environ.get("FRONTEND_URL")
    if extra and extra not in origins:
        origins.append(extra)
    if not _IS_PRODUCTION:
        origins.append("http://localhost:8081")
        if os.environ.get("ALLOW_ALL_ORIGINS"):
            return ["*"]
    return origins


@asynccontextmanager
async def lifespan(app):
    _admin_password()
    try:
        Base.metadata.create_all(bind=get_engine())
    except Exception:
        pass
    yield

app = FastAPI(
    title="NathMaker API",
    lifespan=lifespan,
    docs_url="/docs" if _ENABLE_DOCS else None,
    redoc_url="/redoc" if _ENABLE_DOCS else None,
    openapi_url="/openapi.json" if _ENABLE_DOCS else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
templates.env.globals["docs_enabled"] = _ENABLE_DOCS

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


def require_admin(request: Request) -> None:
    if request.cookies.get("admin_token") != _admin_cookie_value():
        raise HTTPException(status_code=401, detail="Unauthorized")


def enforce_admin(request: Request):
    if request.cookies.get("admin_token") != _admin_cookie_value():
        raise HTTPException(status_code=302, headers={"Location": "/admin/login"})


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _login_allowed(ip: str) -> bool:
    now = time.time()
    recent = [t for t in _login_failures.get(ip, []) if now - t < LOGIN_WINDOW_SECONDS]
    _login_failures[ip] = recent
    return len(recent) < LOGIN_MAX_FAILURES


def _record_login_failure(ip: str) -> None:
    _login_failures.setdefault(ip, []).append(time.time())


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

@api_router.get("/health")
def health():
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")

@api_router.get("/catalogues", response_model=List[CatalogueSchema])
def get_all_catalogues(db: Session = Depends(get_db)):
    ensure_tables()
    return db.query(models.Catalogue).all()

@api_router.post("/catalogues", response_model=CatalogueSchema, status_code=201)
def create_catalogue(
    cat: CatalogueCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
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
def create_product(
    prod: ProductCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
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
def update_product(
    product_id: int,
    updated: ProductCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
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
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}

@api_router.get("/upload-status")
def upload_status():
    return blob_status()

@api_router.post("/upload")
def upload_image(file: UploadFile = File(...), _: None = Depends(require_admin)):
    if not blob_configured():
        raise HTTPException(
            status_code=500,
            detail="Vercel Blob is not configured. Create a public Blob store in the Vercel project Storage tab.",
        )
    content_type = normalize_image_type(file.content_type or "", file.filename or "")
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPEG, PNG, WebP, and GIF images are allowed.",
        )
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file.")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="Image is too large (max 4 MB).")
    try:
        image_url = upload_image_bytes(data, file.filename or "image.jpg", content_type)
        return {"imageUrl": image_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(api_router)

# ─── Admin Endpoints ──────────────────────────────────────────────────────────

@app.get("/admin", response_class=RedirectResponse)
def admin_redirect():
    return RedirectResponse(url="/admin/dashboard")

@app.get("/admin/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/admin/login")
def login_submit(request: Request, password: str = Form(...)):
    ip = _client_ip(request)
    if not _login_allowed(ip):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Too many attempts. Try again later."},
            status_code=429,
        )
    if password == _admin_password():
        _login_failures.pop(ip, None)
        response = RedirectResponse(url="/admin/dashboard", status_code=302)
        response.set_cookie(
            key="admin_token",
            value=_admin_cookie_value(),
            httponly=True,
            secure=_cookie_secure(),
            samesite="lax",
            path="/",
        )
        return response
    _record_login_failure(ip)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid password"})

@app.get("/admin/logout")
def logout():
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("admin_token", path="/")
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

@app.get("/admin/products/bulk", response_class=HTMLResponse)
def admin_products_bulk(request: Request, db: Session = Depends(get_db)):
    enforce_admin(request)
    catalogues = db.query(models.Catalogue).all()
    return templates.TemplateResponse("products_bulk.html", {
        "request": request,
        "catalogues": catalogues
    })

@app.get("/admin/products/bulk/template.xlsx")
def admin_products_bulk_template(request: Request):
    enforce_admin(request)
    return Response(
        content=build_template_xlsx(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=nathmakers-products.xlsx"},
    )

@app.post("/api/products/excel-parse")
def parse_product_excel(
    file: UploadFile = File(...),
    _: None = Depends(require_admin),
):
    filename = file.filename or "products.xlsx"
    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty spreadsheet.")
    try:
        rows = parse_spreadsheet(filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read that spreadsheet. Use .xlsx or .csv.")
    if not rows:
        raise HTTPException(status_code=400, detail="No product rows found.")
    return {"rows": rows}

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

if os.path.isdir(PUBLIC_DIR) and not os.environ.get("TESTING"):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    @app.get("/", response_class=HTMLResponse)
    def serve_index():
        return FileResponse(os.path.join(PUBLIC_DIR, "index.html"))

    app.mount("/", StaticFiles(directory=PUBLIC_DIR, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.index:app", host="0.0.0.0", port=8081, reload=True)

