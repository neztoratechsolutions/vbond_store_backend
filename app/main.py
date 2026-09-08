from fastapi import FastAPI

from app.database import Base, engine
from app.models.customer import Customer

# routers

from app.routers import customer


app = FastAPI(
    title="VBOND Store API",
    version="1.0.0",
)



# Include routers
app.include_router(customer.router)