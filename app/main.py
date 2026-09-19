from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine

# Models
from app.models.user import User
from app.models.customer import Customer
from app.models.customer_address import CustomerAddress
from app.models.category import Category
from app.models.subcategory import Subcategory
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.order import Order

# Routers
from app.routers.auth import router as auth_router
from app.routers import customer
from app.routers import address
from app.routers import admin
from app.routers import unit
from app.routers import product
from app.routers import category
from app.routers import subcategory
from app.routers import product_image
from app.routers import order
from app.routers import order_report


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="VBOND Store API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)


# ==========================================================
# ROUTERS
# ==========================================================

app.include_router(auth_router)

app.include_router(customer.router)

app.include_router(admin.router)

app.include_router(unit.router)

app.include_router(product.router)

app.include_router(address.router)

app.include_router(category.router)

app.include_router(subcategory.router)

app.include_router(product_image.router)

app.include_router(order.router)

app.include_router(order_report.router)