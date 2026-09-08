from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
)

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150), nullable=False)

    email = Column(
        String(150),
        nullable=False,
        unique=True,
        index=True
    )

    phone = Column(
        String(20),
        nullable=False,
        unique=True,
        index=True
    )

    password = Column(
        String(255),
        nullable=True
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    role = Column(
        String(50),
        nullable=False,
        default="CUSTOMER",
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