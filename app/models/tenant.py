from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.orm import relationship
from app.models.base import UUIDMixin, TimestampMixin
from app.database import Base


class Tenant(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "tenants"

    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Quotas
    max_documents = Column(Integer, default=100, nullable=False)
    max_queries_per_day = Column(Integer, default=1000, nullable=False)

    # Relationships
    users = relationship("User", back_populates="tenant",
                         cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="tenant",
                             cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant slug={self.slug}>"
