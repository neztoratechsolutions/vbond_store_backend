from fastapi import FastAPI
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

# Routers
from app.routers.auth import router as auth_router
from app.routers import customer
from app.routers import address
from app.routers import admin
from app.routers import unit
from app.routers import category
from app.routers import subcategory
from app.routers import product_image


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="VBOND Store API",
    version="1.0.0",
)


app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)


# Authentication
app.include_router(auth_router)

# Customer
app.include_router(customer.router)

# Admin
app.include_router(admin.router)

# Unit
app.include_router(unit.router)

# Address
app.include_router(address.router)

# Category
app.include_router(category.router)

# Subcategory
app.include_router(subcategory.router)

# Product Images
app.include_router(product_image.router)


