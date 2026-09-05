from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Numeric,
    ForeignKey,
)
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    subcategory_id = Column(
        Integer,
        ForeignKey("subcategories.id"),
        nullable=False,
        index=True
    )

    unit_id = Column(
        Integer,
        ForeignKey("units.id"),
        nullable=False,
        index=True
    )

    name = Column(String(200), nullable=False)

    slug = Column(
        String(220),
        nullable=False,
        unique=True,
        index=True
    )

    description = Column(Text, nullable=True)

    sku = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True
    )

    price = Column(Numeric(10, 2), nullable=False)

    mrp = Column(Numeric(10, 2), nullable=True)

    discount_price = Column(Numeric(10, 2), nullable=True)

    tax_percentage = Column(
        Numeric(5, 2),
        default=0
    )

    is_available = Column(Boolean, default=True)

    is_active = Column(Boolean, default=True)

    display_order = Column(Integer, default=0)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )