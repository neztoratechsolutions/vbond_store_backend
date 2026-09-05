from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
)
from app.database import Base


class Subcategory(Base):
    __tablename__ = "subcategories"

    id = Column(Integer, primary_key=True, index=True)

    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=False,
        index=True
    )

    name = Column(String(150), nullable=False)

    slug = Column(
        String(180),
        nullable=False,
        unique=True,
        index=True
    )

    description = Column(Text, nullable=True)

    image = Column(String(255), nullable=True)

    is_active = Column(Boolean, default=True)

    display_order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )