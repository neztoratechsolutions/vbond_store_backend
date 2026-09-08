from fastapi import FastAPI

from app.database import Base, engine
from app.models.customer import Customer
from app.models.customer_address import CustomerAddress

# routers

from app.routers import customer
from app.routers import address


app = FastAPI(
    title="VBOND Store API",
    version="1.0.0",
)



# Include routers
app.include_router(customer.router)
app.include_router(address.router)