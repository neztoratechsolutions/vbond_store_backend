from pydantic import BaseModel
from typing import Optional


# ==========================================================
# UPDATE PRODUCT IMAGE
# ==========================================================

class ProductImageUpdate(BaseModel):
    display_order: Optional[int] = None