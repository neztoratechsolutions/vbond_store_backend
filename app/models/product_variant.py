from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Numeric,
    ForeignKey,
)
from app.database import Base


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
        index=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    quantity = Column(
        Numeric(10, 2),
        nullable=False
    )

    sku = Column(
        String(100),
        unique=True,
        nullable=True,
        index=True
    )

    is_available = Column(
        Boolean,
        default=True
    )

    is_active = Column(
        Boolean,
        default=True
    )

    display_order = Column(
        Integer,
        default=0
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