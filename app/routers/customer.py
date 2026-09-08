from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.database import get_db
from app.models.customer import Customer
from app.schemas.customer import (
    CustomerCreate,
    CustomerResponse,
    CustomerUpdate
)


router = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ==========================================================
# CREATE CUSTOMER
# ==========================================================

@router.post(
    "/",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED
)
def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db)
):

    if customer_data.email:

        existing_email = (
            db.query(Customer)
            .filter(Customer.email == customer_data.email)
            .first()
        )

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )

    existing_phone = (
        db.query(Customer)
        .filter(Customer.phone == customer_data.phone)
        .first()
    )

    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already exists"
        )

    password_hash = None

    if customer_data.password:
        password_hash = pwd_context.hash(
            customer_data.password
        )

    customer = Customer(
        name=customer_data.name,
        email=customer_data.email,
        phone=customer_data.phone,
        password_hash=password_hash
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


# ==========================================================
# GET ALL CUSTOMERS
# ==========================================================

@router.get(
    "/",
    response_model=list[CustomerResponse],
    status_code=status.HTTP_200_OK
)
def get_all_customers(
    db: Session = Depends(get_db)
):

    customers = (
        db.query(Customer)
        .order_by(Customer.id.desc())
        .all()
    )

    return customers


# ==========================================================
# GET CUSTOMER BY ID
# ==========================================================

@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    status_code=status.HTTP_200_OK
)
def get_customer_by_id(
    customer_id: int,
    db: Session = Depends(get_db)
):

    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    return customer


# ==========================================================
# UPDATE CUSTOMER
# ==========================================================

@router.put(
    "/{customer_id}",
    response_model=CustomerResponse,
    status_code=status.HTTP_200_OK
)
def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db)
):

    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # Update name
    if customer_data.name is not None:
        customer.name = customer_data.name

    # Update email
    if customer_data.email is not None:

        existing_email = (
            db.query(Customer)
            .filter(
                Customer.email == customer_data.email,
                Customer.id != customer_id
            )
            .first()
        )

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )

        customer.email = customer_data.email

    # Update phone
    if customer_data.phone is not None:

        existing_phone = (
            db.query(Customer)
            .filter(
                Customer.phone == customer_data.phone,
                Customer.id != customer_id
            )
            .first()
        )

        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already exists"
            )

        customer.phone = customer_data.phone

    # Update password
    if customer_data.password is not None:

        customer.password_hash = pwd_context.hash(
            customer_data.password
        )

    # Update active status
    if customer_data.is_active is not None:
        customer.is_active = customer_data.is_active

    db.commit()
    db.refresh(customer)

    return customer


# ==========================================================
# DELETE CUSTOMER
# ==========================================================

@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_200_OK
)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db)
):

    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    db.delete(customer)
    db.commit()

    return {
        "status_code": status.HTTP_200_OK,
        "message": "Customer deleted successfully"
    }