from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.models.customer import Customer
from app.models.customer_address import CustomerAddress
from app.models.category import Category
from app.models.subcategory import Subcategory
from app.models.product import Product
from app.models.product_image import ProductImage

# routers

from app.routers import customer
from app.routers import address
from app.routers import category
from app.routers import subcategory
from app.routers import product_image


app = FastAPI(
    title="VBOND Store API",
    version="1.0.0",
)


# Static files
app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)



# Include routers
app.include_router(customer.router)
app.include_router(address.router)
app.include_router(category.router)
app.include_router(subcategory.router)
app.include_router(product_image.router)