from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
)

from app.database import Base


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False,
        unique=True,
        index=True
    )

    delivery_status = Column(
        String(50),
        nullable=False,
        default="PENDING"
    )

    delivery_person_name = Column(
        String(150),
        nullable=True
    )

    delivery_person_phone = Column(
        String(20),
        nullable=True
    )

    tracking_number = Column(
        String(100),
        nullable=True,
        unique=True,
        index=True
    )

    estimated_delivery_date = Column(
        DateTime,
        nullable=True
    )

    picked_up_at = Column(
        DateTime,
        nullable=True
    )

    delivered_at = Column(
        DateTime,
        nullable=True
    )

    delivery_note = Column(
        Text,
        nullable=True
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