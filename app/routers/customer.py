from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status
)

from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import date, datetime, time, timedelta



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
    page: int | None = Query(
        None,
        ge=1,
        description="Optional page number"
    ),
    start_date: date | None = Query(
        None,
        description="Start date in YYYY-MM-DD format"
    ),
    end_date: date | None = Query(
        None,
        description="End date in YYYY-MM-DD format"
    ),
    db: Session = Depends(get_db)
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date cannot be greater than end date"
        )

    query = db.query(Customer)

    # Start date filter
    if start_date:
        start_datetime = datetime.combine(
            start_date,
            time.min
        )

        query = query.filter(
            Customer.created_at >= start_datetime
        )

    # End date filter - inclusive
    if end_date:
        next_day = end_date + timedelta(days=1)

        end_datetime = datetime.combine(
            next_day,
            time.min
        )

        query = query.filter(
            Customer.created_at < end_datetime
        )

    query = query.order_by(Customer.id.desc())

    # Pagination only when page is provided
    if page is not None:
        page_size = 10

        offset = (page - 1) * page_size

        query = query.offset(offset).limit(page_size)

    customers = query.all()

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