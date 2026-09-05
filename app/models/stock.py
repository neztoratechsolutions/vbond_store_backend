from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    Boolean,
    DateTime,
    ForeignKey,
)

from app.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
        unique=True,
        index=True
    )

    current_stock = Column(
        Numeric(10, 2),
        nullable=False,
        default=0
    )

    minimum_stock = Column(
        Numeric(10, 2),
        nullable=False,
        default=0
    )

    is_available = Column(
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