from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
)
from app.database import Base


class CustomerAddress(Base):
    __tablename__ = "customer_addresses"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False,
        index=True
    )

    address_type = Column(
        String(50),
        nullable=False
    )

    name = Column(
        String(150),
        nullable=False
    )

    phone = Column(
        String(20),
        nullable=False
    )

    address_line_1 = Column(
        String(255),
        nullable=False
    )

    address_line_2 = Column(
        String(255),
        nullable=True
    )

    city = Column(
        String(100),
        nullable=False
    )

    state = Column(
        String(100),
        nullable=False
    )

    pincode = Column(
        String(10),
        nullable=False
    )

    landmark = Column(
        String(255),
        nullable=True
    )

    is_default = Column(
        Boolean,
        default=False
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