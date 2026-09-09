from pydantic import BaseModel
from typing import Optional


# ==========================================================
# CREATE SUBCATEGORY
# ==========================================================

class SubcategoryCreate(BaseModel):
    category_id: int
    name: str
    is_active: bool = True


# ==========================================================
# BULK CREATE SUBCATEGORIES
# ==========================================================

class SubcategoryBulkCreate(BaseModel):
    subcategories: list[SubcategoryCreate]


# ==========================================================
# UPDATE SUBCATEGORY
# ==========================================================

class SubcategoryUpdate(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None