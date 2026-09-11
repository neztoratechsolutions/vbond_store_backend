from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.models.customer import Customer
from app.models.customer_address import CustomerAddress

from app.schemas.address import (
    CustomerAddressCreate,
    CustomerAddressUpdate,
    CustomerAddressResponse
)


router = APIRouter(
    prefix="/customer-addresses",
    tags=["Customer Addresses"]
)


# ==========================================================
# CREATE CUSTOMER ADDRESS
# ==========================================================

@router.post(
    "/",
    response_model=CustomerAddressResponse,
    status_code=status.HTTP_201_CREATED
)
def create_customer_address(
    address_data: CustomerAddressCreate,
    db: Session = Depends(get_db)
):

    # Validate address type
    if address_data.address_type.lower() not in ["home", "office"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Address type must be either home or office"
        )

    # Check customer
    customer = (
        db.query(Customer)
        .filter(Customer.id == address_data.customer_id)
        .first()
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # If new address is default,
    # remove default from existing addresses
    if address_data.is_default:

        db.query(CustomerAddress).filter(
            CustomerAddress.customer_id == address_data.customer_id,
            CustomerAddress.is_default == True
        ).update(
            {
                CustomerAddress.is_default: False
            }
        )

    address = CustomerAddress(
        customer_id=address_data.customer_id,
        address_type=address_data.address_type.lower(),
        name=address_data.name,
        phone=address_data.phone,
        address_line_1=address_data.address_line_1,
        address_line_2=address_data.address_line_2,
        city=address_data.city,
        state=address_data.state,
        pincode=address_data.pincode,
        landmark=address_data.landmark,
        is_default=address_data.is_default
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    return address


# ==========================================================
# GET ALL CUSTOMER ADDRESSES
# ==========================================================

@router.get(
    "/",
    response_model=list[CustomerAddressResponse],
    status_code=status.HTTP_200_OK
)
def get_all_customer_addresses(
    db: Session = Depends(get_db)
):

    addresses = (
        db.query(CustomerAddress)
        .order_by(CustomerAddress.id.desc())
        .all()
    )

    return addresses


# ==========================================================
# GET ADDRESS BY ID
# ==========================================================

@router.get(
    "/{address_id}",
    response_model=CustomerAddressResponse,
    status_code=status.HTTP_200_OK
)
def get_customer_address(
    address_id: int,
    db: Session = Depends(get_db)
):

    address = (
        db.query(CustomerAddress)
        .filter(CustomerAddress.id == address_id)
        .first()
    )

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer address not found"
        )

    return address


# ==========================================================
# GET ADDRESSES BY CUSTOMER ID
# ==========================================================

@router.get(
    "/customer/{customer_id}",
    response_model=list[CustomerAddressResponse],
    status_code=status.HTTP_200_OK
)
def get_addresses_by_customer(
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

    addresses = (
        db.query(CustomerAddress)
        .filter(
            CustomerAddress.customer_id == customer_id
        )
        .order_by(CustomerAddress.id.desc())
        .all()
    )

    return addresses


# ==========================================================
# UPDATE CUSTOMER ADDRESS
# ==========================================================

@router.put(
    "/{address_id}",
    response_model=CustomerAddressResponse,
    status_code=status.HTTP_200_OK
)
def update_customer_address(
    address_id: int,
    address_data: CustomerAddressUpdate,
    db: Session = Depends(get_db)
):

    address = (
        db.query(CustomerAddress)
        .filter(CustomerAddress.id == address_id)
        .first()
    )

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer address not found"
        )

    # Address type
    if address_data.address_type is not None:

        if address_data.address_type.lower() not in [
            "home",
            "office"
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Address type must be either home or office"
            )

        address.address_type = (
            address_data.address_type.lower()
        )

    # Update fields
    if address_data.name is not None:
        address.name = address_data.name

    if address_data.phone is not None:
        address.phone = address_data.phone

    if address_data.address_line_1 is not None:
        address.address_line_1 = address_data.address_line_1

    if address_data.address_line_2 is not None:
        address.address_line_2 = address_data.address_line_2

    if address_data.city is not None:
        address.city = address_data.city

    if address_data.state is not None:
        address.state = address_data.state

    if address_data.pincode is not None:
        address.pincode = address_data.pincode

    if address_data.landmark is not None:
        address.landmark = address_data.landmark

    # Default address
    if address_data.is_default is True:

        db.query(CustomerAddress).filter(
            CustomerAddress.customer_id == address.customer_id,
            CustomerAddress.id != address_id,
            CustomerAddress.is_default == True
        ).update(
            {
                CustomerAddress.is_default: False
            }
        )

        address.is_default = True

    elif address_data.is_default is False:

        address.is_default = False

    # Active status
    if address_data.is_active is not None:
        address.is_active = address_data.is_active

    db.commit()
    db.refresh(address)

    return address


# ==========================================================
# DELETE CUSTOMER ADDRESS
# ==========================================================

@router.delete(
    "/{address_id}",
    status_code=status.HTTP_200_OK
)
def delete_customer_address(
    address_id: int,
    db: Session = Depends(get_db)
):

    address = (
        db.query(CustomerAddress)
        .filter(CustomerAddress.id == address_id)
        .first()
    )

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer address not found"
        )

    db.delete(address)
    db.commit()

    return {
        "status_code": status.HTTP_200_OK,
        "message": "Customer address deleted successfully"
    }