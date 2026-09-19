# ==========================================================
# ORDER ROUTER
# ==========================================================

import os
import smtplib

from datetime import datetime, date, time, timedelta
from decimal import Decimal
from email.message import EmailMessage
from typing import Any, Optional
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.delivery import Delivery
from app.models.order_status_history import OrderStatusHistory
from app.models.user import User

from app.schemas.order import (
    OrderCreate,
    AdminOrderUpdate
)

from app.dependencies import require_role


load_dotenv()


router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


# ==========================================================
# GENERATE SHORT ORDER NUMBER
# Format: VS-16092026-01
# ==========================================================

def generate_order_number(db: Session) -> str:

    today = datetime.utcnow().strftime("%d%m%Y")

    prefix = f"VS-{today}-"

    last_order = (
        db.query(Order)
        .filter(
            Order.order_number.like(f"{prefix}%")
        )
        .order_by(Order.id.desc())
        .first()
    )

    if last_order:

        last_sequence = int(
            last_order.order_number.split("-")[-1]
        )

        next_sequence = last_sequence + 1

    else:

        next_sequence = 1

    return f"{prefix}{next_sequence:02d}"


# ==========================================================
# SEND ORDER DETAILS TO ADMIN EMAIL
# ==========================================================

def send_order_email(
    order: Order,
    order_items: list[OrderItem]
) -> None:

    admin_email = os.getenv("ADMIN_EMAIL")
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_PASSWORD")

    smtp_host = os.getenv(
        "SMTP_HOST",
        "smtp.gmail.com"
    )

    smtp_port = int(
        os.getenv("SMTP_PORT", "587")
    )

    # ------------------------------------------------------
    # CHECK SMTP SETTINGS
    # ------------------------------------------------------

    if not admin_email or not smtp_email or not smtp_password:

        print(
            "Order email skipped: SMTP settings are missing"
        )

        return

    # ------------------------------------------------------
    # CUSTOMER DETAILS
    # ------------------------------------------------------

    customer_details = order.customer_details or {}

    customer_name = customer_details.get(
        "name",
        ""
    )

    customer_email = customer_details.get(
        "email",
        ""
    )

    customer_phone = customer_details.get(
        "phone",
        ""
    )

    address_type = customer_details.get(
        "address_type",
        ""
    )

    address_line_1 = customer_details.get(
        "address_line_1",
        ""
    )

    address_line_2 = customer_details.get(
        "address_line_2",
        ""
    )

    city = customer_details.get(
        "city",
        ""
    )

    state = customer_details.get(
        "state",
        ""
    )

    pincode = customer_details.get(
        "pincode",
        ""
    )

    landmark = customer_details.get(
        "landmark",
        ""
    )

    # ------------------------------------------------------
    # PRODUCT DETAILS
    # ------------------------------------------------------

    product_details = ""

    for index, item in enumerate(
        order_items,
        start=1
    ):

        product_details += f"""
Product {index}
------------------------------

Product Name: {item.product_name}
Product ID: {item.product_id}
Quantity: {item.quantity}
Unit Price: {item.unit_price}
Discount Amount: {item.discount_amount}
Tax Amount: {item.tax_amount}
Product Total: {item.total_price}

"""

    # ------------------------------------------------------
    # EMAIL SUBJECT
    # ------------------------------------------------------

    subject = (
        f"New Order Received - "
        f"{order.order_number}"
    )

    # ------------------------------------------------------
    # EMAIL BODY
    # ------------------------------------------------------

    body = f"""
New Order Received

Order Number: {order.order_number}
Order Date: {order.created_at}

==============================
CUSTOMER DETAILS
==============================

Name: {customer_name}
Email: {customer_email}
Phone: {customer_phone}

==============================
DELIVERY ADDRESS
==============================

Address Type: {address_type}
Address Line 1: {address_line_1}
Address Line 2: {address_line_2}
City: {city}
State: {state}
Pincode: {pincode}
Landmark: {landmark}

==============================
PRODUCT DETAILS
==============================

{product_details}

==============================
ORDER DETAILS
==============================

Subtotal: {order.subtotal}
Discount Amount: {order.discount_amount}
Tax Amount: {order.tax_amount}
Delivery Charge: {order.delivery_charge}
Total Amount: {order.total_amount}

Payment Method: {order.payment_method}
Payment Status: {order.payment_status}
Order Status: {order.order_status}

Customer Note: {order.customer_note or "No note"}

==============================
VBOND STORE
==============================
"""

    # ------------------------------------------------------
    # CREATE EMAIL
    # ------------------------------------------------------

    message = EmailMessage()

    message["From"] = smtp_email
    message["To"] = admin_email
    message["Subject"] = subject

    message.set_content(body)

    # ------------------------------------------------------
    # SEND EMAIL
    # ------------------------------------------------------

    try:

        print(
            f"Sending order email: {order.order_number}"
        )

        with smtplib.SMTP(
            smtp_host,
            smtp_port,
            timeout=30
        ) as server:

            server.ehlo()

            server.starttls()

            server.ehlo()

            server.login(
                smtp_email,
                smtp_password
            )

            server.send_message(message)

        print(
            f"Order email sent successfully: "
            f"{order.order_number}"
        )

    except Exception as error:

        print(
            f"Order email failed: {error}"
        )


# ==========================================================
# CREATE ORDER - MULTIPLE PRODUCTS
# ==========================================================

@router.post(
    "/create",
    status_code=status.HTTP_201_CREATED
)
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db)
):

    # ------------------------------------------------------
    # VALIDATE PRODUCTS
    # ------------------------------------------------------

    if not data.products:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one product is required"
        )

    # ------------------------------------------------------
    # GENERATE ORDER NUMBER
    # ------------------------------------------------------

    order_number = generate_order_number(db)

    customer_details = (
        data.customer_details.model_dump()
    )

    # ------------------------------------------------------
    # TOTAL CALCULATIONS
    # ------------------------------------------------------

    subtotal = Decimal("0.00")
    total_discount = Decimal("0.00")
    total_tax = Decimal("0.00")
    delivery_charge = Decimal("0.00")

    order_items_data = []

    # ------------------------------------------------------
    # VALIDATE EACH PRODUCT
    # ------------------------------------------------------

    for product_data in data.products:

        product = (
            db.query(Product)
            .filter(
                Product.id == product_data.product_id,
                Product.is_active.is_(True),
                Product.is_available.is_(True)
            )
            .first()
        )

        if not product:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Product with id "
                    f"{product_data.product_id} "
                    f"not found or unavailable"
                )
            )

        quantity = Decimal(
            str(product_data.quantity)
        )

        if quantity <= 0:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Quantity must be greater than zero "
                    f"for product {product.id}"
                )
            )

        # --------------------------------------------------
        # PRICE
        # --------------------------------------------------

        unit_price = Decimal(
            str(product.price)
        )

        item_subtotal = (
            unit_price * quantity
        )

        # --------------------------------------------------
        # DISCOUNT
        # --------------------------------------------------

        item_discount = Decimal(
            "0.00"
        )

        # --------------------------------------------------
        # TAX
        # --------------------------------------------------

        tax_percentage = Decimal(
            str(product.tax_percentage or 0)
        )

        taxable_amount = (
            item_subtotal - item_discount
        )

        item_tax = (
            taxable_amount
            * tax_percentage
        ) / Decimal("100")

        # --------------------------------------------------
        # ITEM TOTAL
        # --------------------------------------------------

        item_total = (
            taxable_amount
            + item_tax
        )

        # --------------------------------------------------
        # ADD TO ORDER TOTAL
        # --------------------------------------------------

        subtotal += item_subtotal
        total_discount += item_discount
        total_tax += item_tax

        # --------------------------------------------------
        # STORE ITEM DATA
        # --------------------------------------------------

        order_items_data.append({

            "product_id": product.id,

            "product_name": product.name,

            "quantity": quantity,

            "unit_price": unit_price,

            "discount_amount": item_discount,

            "tax_amount": item_tax,

            "total_price": item_total

        })

    # ------------------------------------------------------
    # FINAL ORDER TOTAL
    # ------------------------------------------------------

    taxable_amount = (
        subtotal - total_discount
    )

    total_amount = (
        taxable_amount
        + total_tax
        + delivery_charge
    )

    # ------------------------------------------------------
    # CREATE ORDER
    # ------------------------------------------------------

    order = Order(

        order_number=order_number,

        customer_details=customer_details,

        subtotal=subtotal,

        discount_amount=total_discount,

        tax_amount=total_tax,

        delivery_charge=delivery_charge,

        total_amount=total_amount,

        payment_method=data.payment_method,

        payment_status="PENDING",

        order_status="PENDING",

        customer_note=data.customer_note,

        is_active=True
    )

    db.add(order)

    db.flush()

    # ------------------------------------------------------
    # CREATE MULTIPLE ORDER ITEMS
    # ------------------------------------------------------

    created_items = []

    for item_data in order_items_data:

        order_item = OrderItem(

            order_id=order.id,

            product_id=item_data["product_id"],

            product_name=item_data["product_name"],

            quantity=item_data["quantity"],

            unit_price=item_data["unit_price"],

            discount_amount=item_data["discount_amount"],

            tax_amount=item_data["tax_amount"],

            total_price=item_data["total_price"]
        )

        db.add(order_item)

        created_items.append(order_item)

    # ------------------------------------------------------
    # SAVE ORDER
    # ------------------------------------------------------

    try:

        db.commit()

        db.refresh(order)

        for item in created_items:

            db.refresh(item)

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order creation failed"
        )

    # ------------------------------------------------------
    # SEND EMAIL AFTER DB COMMIT
    # ------------------------------------------------------

    send_order_email(
        order,
        created_items
    )

    # ------------------------------------------------------
    # RESPONSE PRODUCTS
    # ------------------------------------------------------

    products_response = []

    for item in created_items:

        products_response.append({

            "product_id": item.product_id,

            "product_name": item.product_name,

            "quantity": item.quantity,

            "unit_price": item.unit_price,

            "discount_amount": item.discount_amount,

            "tax_amount": item.tax_amount,

            "total_price": item.total_price

        })

    # ------------------------------------------------------
    # RESPONSE
    # ------------------------------------------------------

    return {

        "status": True,

        "message": "Order created successfully",

        "data": {

            "order_id": order.id,

            "order_number": order.order_number,

            "customer_details": order.customer_details,

            "products": products_response,

            "subtotal": order.subtotal,

            "discount_amount": order.discount_amount,

            "tax_amount": order.tax_amount,

            "delivery_charge": order.delivery_charge,

            "total_amount": order.total_amount,

            "payment_method": order.payment_method,

            "payment_status": order.payment_status,

            "order_status": order.order_status,

            "customer_note": order.customer_note,

            "created_at": order.created_at

        }

    }


# ==========================================================
# CUSTOMER ORDER HISTORY BY PHONE
# ==========================================================

@router.get("/customer-orders")
def get_customer_order_history(

    phone: str = Query(
        ...,
        description="Customer phone number"
    ),

    page: int = Query(
        default=1,
        ge=1,
        description="Page number"
    ),

    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Number of orders per page"
    ),

    db: Session = Depends(get_db)
):

    customer_phone = phone.strip()

    # ------------------------------------------------------
    # FIND CUSTOMER ORDERS
    # ------------------------------------------------------

    orders_query = (
        db.query(Order)
        .filter(
            Order.is_active.is_(True),
            Order.customer_details["phone"].as_string()
            == customer_phone
        )
        .order_by(
            Order.created_at.desc()
        )
    )

    # ------------------------------------------------------
    # TOTAL ORDERS
    # ------------------------------------------------------

    total_orders = orders_query.count()

    if total_orders == 0:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No orders found for this customer"
        )

    # ------------------------------------------------------
    # PAGINATION
    # ------------------------------------------------------

    offset = (page - 1) * limit

    orders = (
        orders_query
        .offset(offset)
        .limit(limit)
        .all()
    )

    if not orders:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No orders found for this page"
        )

    total_pages = (
        total_orders + limit - 1
    ) // limit

    # ------------------------------------------------------
    # BUILD ORDER HISTORY
    # ------------------------------------------------------

    order_history = []

    for order in orders:

        # --------------------------------------------------
        # ORDER ITEMS
        # --------------------------------------------------

        items = (
            db.query(OrderItem)
            .filter(
                OrderItem.order_id == order.id
            )
            .all()
        )

        order_items = []

        total_quantity = 0

        for item in items:

            total_quantity += int(
                item.quantity
            )

            order_items.append({

                "product_id": item.product_id,

                "product_name": item.product_name,

                "quantity": item.quantity,

                "unit_price": item.unit_price,

                "total_price": item.total_price

            })

        # --------------------------------------------------
        # ORDER HISTORY RESPONSE
        # --------------------------------------------------

        order_history.append({

            "order_id": order.id,

            "order_number": order.order_number,

            "customer": {

                "name": (
                    order.customer_details.get(
                        "name",
                        ""
                    )
                ),

                "phone_number": customer_phone

            },

            "order_date": order.created_at,

            "products": order_items,

            "total_quantity": total_quantity,

            "subtotal": order.subtotal,

            "discount_amount": (
                order.discount_amount
            ),

            "tax_amount": order.tax_amount,

            "delivery_charge": (
                order.delivery_charge
            ),

            "total_amount": order.total_amount,

            "payment_method": (
                order.payment_method
            ),

            "payment_status": (
                order.payment_status
            ),

            "order_status": (
                order.order_status
            )

        })

    # ------------------------------------------------------
    # FINAL RESPONSE
    # ------------------------------------------------------

    return {

        "status_code": 200,

        "message": (
            "Customer order history "
            "fetched successfully"
        ),

        "customer": {

            "phone_number": customer_phone,

            "total_orders": total_orders

        },

        "pagination": {

            "current_page": page,

            "per_page": limit,

            "total_orders": total_orders,

            "total_pages": total_pages,

            "has_next_page": (
                page < total_pages
            ),

            "has_previous_page": (
                page > 1
            )

        },

        "orders": order_history

    }



# ==========================================================
# GET ORDER BY ID
# ==========================================================

@router.get("/{order_id}")
def get_order_by_id(

    order_id: int,

    db: Session = Depends(get_db)
):

    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.is_active.is_(True)
        )
        .first()
    )

    if not order:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    order_items = (
        db.query(OrderItem)
        .filter(
            OrderItem.order_id == order.id
        )
        .all()
    )

    if not order_items:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order items not found"
        )

    return {

        "status": True,

        "message": "Order fetched successfully",

        "data": {

            "order_id": order.id,

            "order_number": order.order_number,

            "customer_details": order.customer_details,

            "items": [

                {

                    "product_id": item.product_id,

                    "product_name": item.product_name,

                    "quantity": item.quantity,

                    "unit_price": item.unit_price,

                    "discount_amount": item.discount_amount,

                    "tax_amount": item.tax_amount,

                    "total_price": item.total_price

                }

                for item in order_items

            ],

            "subtotal": order.subtotal,

            "discount_amount": order.discount_amount,

            "tax_amount": order.tax_amount,

            "delivery_charge": order.delivery_charge,

            "total_amount": order.total_amount,

            "payment_method": order.payment_method,

            "payment_status": order.payment_status,

            "order_status": order.order_status,

            "customer_note": order.customer_note,

            "created_at": order.created_at

        }

    }


# ==========================================================
# GET INDIA CURRENT DATE
# ==========================================================

def get_india_today() -> date:

    return datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).date()


# ==========================================================
# GET ALL ORDERS
# DEFAULT: INDIA TODAY'S ORDERS ONLY
# WITH DATE FILTER AND PAGINATION
# ==========================================================

@router.get("/")
def get_all_orders(

    start_date: Optional[date] = Query(
        default=None,
        description="Start date in YYYY-MM-DD format"
    ),

    end_date: Optional[date] = Query(
        default=None,
        description="End date in YYYY-MM-DD format"
    ),

    page: int = Query(
        default=1,
        ge=1,
        description="Page number"
    ),

    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Number of orders per page"
    ),

    db: Session = Depends(get_db)
):

    # ------------------------------------------------------
    # DEFAULT DATE = INDIA TODAY
    # ------------------------------------------------------

    today = get_india_today()

    if start_date is None and end_date is None:

        start_date = today
        end_date = today

    elif start_date is not None and end_date is None:

        end_date = start_date

    elif start_date is None and end_date is not None:

        start_date = end_date

    # ------------------------------------------------------
    # VALIDATE DATE RANGE
    # ------------------------------------------------------

    if start_date > end_date:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be greater than end_date"
        )

    # ------------------------------------------------------
    # CONVERT INDIA DATE TO UTC DATETIME
    # ------------------------------------------------------

    india_timezone = ZoneInfo(
        "Asia/Kolkata"
    )

    start_india_datetime = datetime.combine(
        start_date,
        time.min
    ).replace(
        tzinfo=india_timezone
    )

    end_india_datetime = datetime.combine(
        end_date + timedelta(days=1),
        time.min
    ).replace(
        tzinfo=india_timezone
    )

    start_utc_datetime = (
        start_india_datetime
        .astimezone(
            ZoneInfo("UTC")
        )
        .replace(
            tzinfo=None
        )
    )

    end_utc_datetime = (
        end_india_datetime
        .astimezone(
            ZoneInfo("UTC")
        )
        .replace(
            tzinfo=None
        )
    )

    # ------------------------------------------------------
    # FILTER ORDERS
    # ------------------------------------------------------

    query = (
        db.query(Order)
        .filter(
            Order.is_active.is_(True),

            Order.created_at >= start_utc_datetime,

            Order.created_at < end_utc_datetime
        )
        .order_by(
            Order.id.desc()
        )
    )

    # ------------------------------------------------------
    # TOTAL COUNT
    # ------------------------------------------------------

    total_orders = query.count()

    if total_orders == 0:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No orders found for "
                "the selected date range"
            )
        )

    # ------------------------------------------------------
    # PAGINATION
    # ------------------------------------------------------

    offset = (
        page - 1
    ) * limit

    orders = (
        query
        .offset(offset)
        .limit(limit)
        .all()
    )

    if not orders:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No orders found for this page"
        )

    total_pages = (
        total_orders + limit - 1
    ) // limit

    # ------------------------------------------------------
    # RESPONSE DATA
    # ------------------------------------------------------

    response_data: list[
        dict[str, Any]
    ] = []

    for order in orders:

        order_items = (
            db.query(OrderItem)
            .filter(
                OrderItem.order_id == order.id
            )
            .all()
        )

        response_data.append({

            "order_id": order.id,

            "order_number": order.order_number,

            "customer_details": (
                order.customer_details
            ),

            "items": [

                {

                    "product_id": item.product_id,

                    "product_name": item.product_name,

                    "quantity": item.quantity,

                    "unit_price": item.unit_price,

                    "discount_amount": (
                        item.discount_amount
                    ),

                    "tax_amount": (
                        item.tax_amount
                    ),

                    "total_price": (
                        item.total_price
                    )

                }

                for item in order_items

            ],

            "subtotal": order.subtotal,

            "discount_amount": (
                order.discount_amount
            ),

            "tax_amount": order.tax_amount,

            "delivery_charge": (
                order.delivery_charge
            ),

            "total_amount": (
                order.total_amount
            ),

            "payment_method": (
                order.payment_method
            ),

            "payment_status": (
                order.payment_status
            ),

            "order_status": (
                order.order_status
            ),

            "customer_note": (
                order.customer_note
            ),

            "created_at": (
                order.created_at
            )

        })

    # ------------------------------------------------------
    # FINAL RESPONSE
    # ------------------------------------------------------

    return {

        "status": True,

        "message": "Orders fetched successfully",

        "filters": {

            "start_date": start_date,

            "end_date": end_date

        },

        "pagination": {

            "current_page": page,

            "per_page": limit,

            "total_orders": total_orders,

            "total_pages": total_pages,

            "has_next_page": (
                page < total_pages
            ),

            "has_previous_page": (
                page > 1
            )

        },

        "data": response_data

    }


# ==========================================================
# ADMIN ORDER UPDATE
# ==========================================================

@router.put(
    "/{order_id}/admin-update"
)
def admin_update_order(

    order_id: int,

    data: AdminOrderUpdate,

    current_user: User = Depends(
        require_role("ADMIN")
    ),

    db: Session = Depends(get_db)
):

    # ------------------------------------------------------
    # FIND ORDER
    # ------------------------------------------------------

    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.is_active.is_(True)
        )
        .first()
    )

    if not order:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # ------------------------------------------------------
    # CHECK THAT SOMETHING WAS PROVIDED
    # ------------------------------------------------------

    update_data = data.model_dump(
        exclude_unset=True
    )

    if not update_data:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided"
        )

    # ------------------------------------------------------
    # UPDATE ORDER STATUS
    # ------------------------------------------------------

    if data.order_status is not None:

        old_status = order.order_status

        order.order_status = data.order_status

        if old_status != data.order_status:

            history = OrderStatusHistory(

                order_id=order.id,

                old_status=old_status,

                new_status=data.order_status,

                changed_by=current_user.name,

                note="Order status updated by admin"

            )

            db.add(history)

    # ------------------------------------------------------
    # UPDATE PAYMENT
    # ------------------------------------------------------

    if data.payment_status is not None:

        order.payment_status = data.payment_status

    if data.payment_method is not None:

        order.payment_method = data.payment_method

    # ------------------------------------------------------
    # FIND DELIVERY RECORD
    # ------------------------------------------------------

    delivery = (
        db.query(Delivery)
        .filter(
            Delivery.order_id == order.id
        )
        .first()
    )

    if delivery is None:

        delivery = Delivery(

            order_id=order.id,

            delivery_status="PENDING"

        )

        db.add(delivery)

        db.flush()

    # ------------------------------------------------------
    # UPDATE DELIVERY
    # ------------------------------------------------------

    if data.delivery_status is not None:

        delivery.delivery_status = (
            data.delivery_status
        )

    if data.delivery_person_name is not None:

        delivery.delivery_person_name = (
            data.delivery_person_name
        )

    if data.delivery_person_phone is not None:

        delivery.delivery_person_phone = (
            data.delivery_person_phone
        )

    if data.tracking_number is not None:

        delivery.tracking_number = (
            data.tracking_number
        )

    if data.estimated_delivery_date is not None:

        delivery.estimated_delivery_date = (
            data.estimated_delivery_date
        )

    if data.delivery_note is not None:

        delivery.delivery_note = (
            data.delivery_note
        )

    # ------------------------------------------------------
    # AUTOMATIC DELIVERY TIMESTAMPS
    # ------------------------------------------------------

    if (
        data.delivery_status == "PICKED_UP"
        and delivery.picked_up_at is None
    ):

        delivery.picked_up_at = datetime.utcnow()

    if (
        data.delivery_status == "DELIVERED"
        and delivery.delivered_at is None
    ):

        delivery.delivered_at = datetime.utcnow()

    # ------------------------------------------------------
    # SAVE
    # ------------------------------------------------------

    try:

        db.commit()

        db.refresh(order)

        db.refresh(delivery)

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order update failed"
        )

    # ------------------------------------------------------
    # RESPONSE
    # ------------------------------------------------------

    return {

        "status": True,

        "message": "Order updated successfully",

        "data": {

            "order_id": order.id,

            "order_number": order.order_number,

            "order_status": order.order_status,

            "payment": {

                "payment_method": (
                    order.payment_method
                ),

                "payment_status": (
                    order.payment_status
                )

            },

            "delivery": {

                "delivery_id": delivery.id,

                "delivery_status": (
                    delivery.delivery_status
                ),

                "delivery_person_name": (
                    delivery.delivery_person_name
                ),

                "delivery_person_phone": (
                    delivery.delivery_person_phone
                ),

                "tracking_number": (
                    delivery.tracking_number
                ),

                "estimated_delivery_date": (
                    delivery.estimated_delivery_date
                ),

                "picked_up_at": (
                    delivery.picked_up_at
                ),

                "delivered_at": (
                    delivery.delivered_at
                ),

                "delivery_note": (
                    delivery.delivery_note
                )

            },

            "updated_by": {

                "user_id": current_user.id,

                "name": current_user.name,

                "role": current_user.role

            },

            "updated_at": order.updated_at

        }

    }


# ==========================================================
# ADMIN ORDER DELETE
# ==========================================================

@router.delete(
    "/{order_id}/admin-delete"
)
def admin_delete_order(

    order_id: int,

    current_user: User = Depends(
        require_role("ADMIN")
    ),

    db: Session = Depends(get_db)
):

    # ------------------------------------------------------
    # FIND ORDER
    # ------------------------------------------------------

    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.is_active.is_(True)
        )
        .first()
    )

    if not order:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # ------------------------------------------------------
    # SOFT DELETE
    # ------------------------------------------------------

    order.is_active = False

    # ------------------------------------------------------
    # SAVE
    # ------------------------------------------------------

    try:

        db.commit()

        db.refresh(order)

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order deletion failed"
        )

    # ------------------------------------------------------
    # RESPONSE
    # ------------------------------------------------------

    return {

        "status": True,

        "message": "Order deleted successfully",

        "data": {

            "order_id": order.id,

            "order_number": order.order_number,

            "is_active": order.is_active,

            "deleted_by": {

                "user_id": current_user.id,

                "name": current_user.name,

                "role": current_user.role

            },

            "deleted_at": order.updated_at

        }

    }