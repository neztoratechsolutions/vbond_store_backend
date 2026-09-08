from pydantic import BaseModel,EmailStr
from typing import Literal

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str
    role: Literal["CUSTOMER","ADMIN"] = "CUSTOMER"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    message: str
    access_token: str
    token_type: str
    user_id: int
    name: str
    email: EmailStr
    role: str