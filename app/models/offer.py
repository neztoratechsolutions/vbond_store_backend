from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Numeric,
)
from app.database import Base


class Offer(Base):
    __tablename__ = "offers"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(150),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    offer_type = Column(
        String(50),
        nullable=False
    )

    discount_value = Column(
        Numeric(10, 2),
        nullable=False
    )

    minimum_amount = Column(
        Numeric(10, 2),
        nullable=True
    )

    maximum_discount = Column(
        Numeric(10, 2),
        nullable=True
    )

    start_date = Column(
        DateTime,
        nullable=False
    )

    end_date = Column(
        DateTime,
        nullable=False
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