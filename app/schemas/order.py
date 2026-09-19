from decimal import Decimal
from typing import Optional

from datetime import datetime

from pydantic import BaseModel, Field


# ==========================================================
# CUSTOMER DETAILS
# ==========================================================

class CustomerDetails(BaseModel):

    name: str = Field(
        ...,
        min_length=1,
        max_length=150
    )

    email: str = Field(
        ...,
        min_length=1,
        max_length=150
    )

    phone: str = Field(
        ...,
        min_length=10,
        max_length=20
    )

    address_type: Optional[str] = Field(
        default="",
        max_length=50
    )

    address_line_1: Optional[str] = Field(
        default="",
        max_length=255
    )

    address_line_2: Optional[str] = ""

    city: Optional[str] = Field(
        default="",
        max_length=100
    )

    state: Optional[str] = Field(
        default="",
        max_length=100
    )

    pincode: Optional[str] = Field(
        default="",
        max_length=10
    )

    landmark: Optional[str] = ""


# ==========================================================
# ORDER PRODUCT
# ==========================================================

class OrderProduct(BaseModel):

    product_id: int = Field(
        ...,
        gt=0
    )

    quantity: Decimal = Field(
        ...,
        gt=0
    )


# ==========================================================
# CREATE ORDER
# ==========================================================

class OrderCreate(BaseModel):

    customer_details: CustomerDetails

    products: list[OrderProduct] = Field(
        ...,
        min_length=1
    )

    payment_method: str = Field(
        default="COD",
        max_length=50
    )

    customer_note: Optional[str] = None


# ==========================================================
# ADMIN ORDER UPDATE
# ==========================================================

class AdminOrderUpdate(BaseModel):

    order_status: Optional[str] = None

    payment_status: Optional[str] = None

    payment_method: Optional[str] = None

    delivery_status: Optional[str] = None

    delivery_person_name: Optional[str] = None

    delivery_person_phone: Optional[str] = None

    tracking_number: Optional[str] = None

    estimated_delivery_date: Optional[datetime] = None

    delivery_note: Optional[str] = None