from decimal import Decimal
from datetime import datetime
from typing import Optional

from pydantic import BaseModel,ConfigDict

class ProductCreate(BaseModel):
    subcategory_id : int
    unit_id : int
    name : str
    sku : str
    display_order : int = 0
    description : Optional[str] = None
    price : Decimal
    mrp : Optional[Decimal] = None
    discount_price: Optional[Decimal] = None
    tax_percentage : Decimal = Decimal("0")
    is_available : bool = True
    is_active : bool = True

class ProductResponse(BaseModel):
    id: int
    subcategory_id: int
    unit_id: int
    name: str
    slug: str
    description: Optional[str] = None
    sku: str
    price: Decimal
    mrp: Optional[Decimal] = None
    discount_price: Optional[Decimal] = None
    tax_percentage: Decimal
    is_available: bool
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)