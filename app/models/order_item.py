from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    ForeignKey,
)

from app.database import Base


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False,
        index=True
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
        index=True
    )

    product_name = Column(
        String(200),
        nullable=False
    )

    quantity = Column(
        Numeric(10, 2),
        nullable=False
    )

    unit_price = Column(
        Numeric(10, 2),
        nullable=False
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

    total_price = Column(
        Numeric(10, 2),
        nullable=False
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