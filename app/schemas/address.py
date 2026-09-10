from pydantic import BaseModel
from typing import Optional


class CustomerAddressCreate(BaseModel):
    customer_id: int
    address_type: str
    name: str
    phone: str
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    pincode: str
    landmark: Optional[str] = None
    is_default: bool = False


class CustomerAddressUpdate(BaseModel):
    address_type: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    landmark: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class CustomerAddressResponse(BaseModel):
    id: int
    customer_id: int
    address_type: str
    name: str
    phone: str
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    pincode: str
    landmark: Optional[str] = None
    is_default: bool
    is_active: bool

    class Config:
        from_attributes = True