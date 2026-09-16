from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Boolean,
    DateTime,
    Text,
    JSON,
)

from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    order_number = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True
    )

    customer_details = Column(
        JSON,
        nullable=False
    )

    subtotal = Column(
        Numeric(10, 2),
        nullable=False,
        default=0
    )

    discount_amount = Column(
        Numeric(10, 2),
        nullable=False,
        default=0
    )

    tax_amount = Column(
        Numeric(10, 2),
        nullable=False,
        default=0
    )

    delivery_charge = Column(
        Numeric(10, 2),
        nullable=False,
        default=0
    )

    total_amount = Column(
        Numeric(10, 2),
        nullable=False,
        default=0
    )

    payment_method = Column(
        String(50),
        nullable=False,
        default="COD"
    )

    payment_status = Column(
        String(50),
        nullable=False,
        default="PENDING"
    )

    order_status = Column(
        String(50),
        nullable=False,
        default="PENDING"
    )

    customer_note = Column(
        Text,
        nullable=True
    )

    is_active = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )