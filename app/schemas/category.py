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
    slug: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None