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


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

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

    old_status = Column(
        String(50),
        nullable=True
    )

    new_status = Column(
        String(50),
        nullable=False
    )

    changed_by = Column(
        String(150),
        nullable=True
    )

    note = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )