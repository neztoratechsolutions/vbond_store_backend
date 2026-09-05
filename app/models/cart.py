from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
)

from app.database import Base


class Cart(Base):
    __tablename__ = "carts"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False,
        unique=True,
        index=True
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