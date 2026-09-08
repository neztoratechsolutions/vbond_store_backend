from fastapi import FastAPI
from app.routers.auth import router as auth_router
from app.routers import customer
from app.routers import admin
from app.database import Base, engine

from app.models.user import User

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="VBOND Store API",
    version="1.0.0",
)

app.include_router(auth_router)
app.include_router(customer.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return {
        "message": "VBOND Store API is running"
    }

    