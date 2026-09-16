from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


# ==========================================================
# CUSTOMER DETAILS
# ==========================================================

class CustomerDetails(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    email: Optional[str] = None
    phone: str = Field(..., min_length=10, max_length=20)

    address_type: str = Field(..., max_length=50)
    address_line_1: str = Field(..., min_length=1, max_length=255)
    address_line_2: Optional[str] = None

    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    pincode: str = Field(..., min_length=4, max_length=10)
    landmark: Optional[str] = None


# ==========================================================
# CREATE ORDER
# ==========================================================

class OrderCreate(BaseModel):
    customer_details: CustomerDetails

    product_id: int = Field(..., gt=0)

    quantity: Decimal = Field(..., gt=0)

    payment_method: str = Field(
        default="COD",
        max_length=50
    )

    customer_note: Optional[str] = None




