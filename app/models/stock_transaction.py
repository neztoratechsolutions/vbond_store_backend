from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    DateTime,
    ForeignKey,
    Text,
)

from app.database import Base


class StockTransaction(Base):
    __tablename__ = "stock_transactions"

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

    transaction_type = Column(
        String(50),
        nullable=False
    )

    quantity = Column(
        Numeric(10, 2),
        nullable=False
    )

    stock_before = Column(
        Numeric(10, 2),
        nullable=False
    )

    stock_after = Column(
        Numeric(10, 2),
        nullable=False
    )

    reference_type = Column(
        String(50),
        nullable=True
    )

    reference_id = Column(
        Integer,
        nullable=True,
        index=True
    )

    note = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )