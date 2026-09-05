from sqlalchemy import Column, String, Integer, Numeric, ForeignKey,Text, Boolean, DateTime, UniqueConstraint, Date
from datetime import datetime, date
from app.database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, unique=True)
    slug = Column(String(180), nullable=False, unique=True, index=True)
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

