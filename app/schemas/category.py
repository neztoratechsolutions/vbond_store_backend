from pydantic import BaseModel
from typing import Optional


# ==========================================================
# SINGLE CATEGORY CREATE
# ==========================================================

class CategoryCreate(BaseModel):
    name: str
    is_active: bool = True


# ==========================================================
# BULK CATEGORY CREATE
# ==========================================================

class CategoryBulkCreate(BaseModel):
    categories: list[CategoryCreate]


# ==========================================================
# CATEGORY UPDATE
# ==========================================================

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None