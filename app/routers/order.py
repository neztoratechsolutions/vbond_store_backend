# ==========================================================
# ORDER ROUTER
# ==========================================================

import os
import smtplib

from datetime import datetime
from decimal import Decimal
from email.message import EmailMessage
from typing import Any

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.schemas.order import OrderCreate


load_dotenv()


router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


# ==========================================================
# GENERATE SHORT ORDER NUMBER
# Format: VS-260914-01
# ==========================================================

def generate_order_number(db: Session) -> str:
    today = datetime.utcnow().strftime("%y%m%d")
    prefix = f"VS-{today}-"

    last_order = (
        db.query(Order)
        .filter(Order.order_number.like(f"{prefix}%"))
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
    order_item: OrderItem
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

    if not admin_email or not smtp_email or not smtp_password:
        print(
            "Order email skipped: SMTP settings are missing"
        )
        return

    customer_details = order.customer_details or {}

    customer_name = customer_details.get("name", "")
    customer_email = customer_details.get("email", "")
    customer_phone = customer_details.get("phone", "")

    address_type = customer_details.get("address_type", "")
    address_line_1 = customer_details.get("address_line_1", "")
    address_line_2 = customer_details.get("address_line_2", "")
    city = customer_details.get("city", "")
    state = customer_details.get("state", "")
    pincode = customer_details.get("pincode", "")
    landmark = customer_details.get("landmark", "")

    subject = (
        f"New Order Received - {order.order_number}"
    )

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

Product Name: {order_item.product_name}
Product ID: {order_item.product_id}
Quantity: {order_item.quantity}
Unit Price: {order_item.unit_price}
Discount Amount: {order_item.discount_amount}
Tax Amount: {order_item.tax_amount}
Product Total: {order_item.total_price}

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

    message = EmailMessage()
    message["From"] = smtp_email
    message["To"] = admin_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(
            smtp_host,
            smtp_port
        ) as server:

            server.starttls()

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
# CREATE ORDER
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
    # VALIDATE PRODUCT
    # ------------------------------------------------------

    product = (
        db.query(Product)
        .filter(
            Product.id == data.product_id,
            Product.is_active.is_(True),
            Product.is_available.is_(True)
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or unavailable"
        )

    if data.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be greater than zero"
        )

    # ------------------------------------------------------
    # PRICE CALCULATION
    # ------------------------------------------------------

    quantity = Decimal(str(data.quantity))
    unit_price = Decimal(str(product.price))

    subtotal = unit_price * quantity

    discount_amount = Decimal("0.00")

    tax_percentage = Decimal(
        str(product.tax_percentage or 0)
    )

    taxable_amount = subtotal - discount_amount

    tax_amount = (
        taxable_amount * tax_percentage
    ) / Decimal("100")

    delivery_charge = Decimal("0.00")

    total_amount = (
        taxable_amount
        + tax_amount
        + delivery_charge
    )

    # ------------------------------------------------------
    # GENERATE ORDER NUMBER
    # ------------------------------------------------------

    order_number = generate_order_number(db)

    customer_details = (
        data.customer_details.model_dump()
    )

    # ------------------------------------------------------
    # CREATE ORDER
    # ------------------------------------------------------

    order = Order(
        order_number=order_number,
        customer_details=customer_details,
        subtotal=subtotal,
        discount_amount=discount_amount,
        tax_amount=tax_amount,
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
    # CREATE ORDER ITEM
    # ------------------------------------------------------

    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        product_name=product.name,
        quantity=quantity,
        unit_price=unit_price,
        discount_amount=discount_amount,
        tax_amount=tax_amount,
        total_price=total_amount
    )

    db.add(order_item)

    # ------------------------------------------------------
    # SAVE ORDER TO DATABASE
    # ------------------------------------------------------

    try:
        db.commit()

        db.refresh(order)
        db.refresh(order_item)

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
        order_item
    )

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

            "product": {
                "product_id": order_item.product_id,
                "product_name": order_item.product_name,
                "quantity": order_item.quantity,
                "unit_price": order_item.unit_price,
                "discount_amount": order_item.discount_amount,
                "tax_amount": order_item.tax_amount,
                "total_price": order_item.total_price
            },

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
# GET ALL ORDERS
# ==========================================================

@router.get("/")
def get_all_orders(
    db: Session = Depends(get_db)
):

    orders = (
        db.query(Order)
        .filter(Order.is_active.is_(True))
        .order_by(Order.id.desc())
        .all()
    )

    if not orders:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No orders found"
        )

    response_data: list[dict[str, Any]] = []

    for order in orders:

        order_items = (
            db.query(OrderItem)
            .filter(
                OrderItem.order_id == order.id
            )
            .all()
        )

        response_data.append(
            {
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
        )

    return {
        "status": True,
        "message": "Orders fetched successfully",
        "data": response_data
    }