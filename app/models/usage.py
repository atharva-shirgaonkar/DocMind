from sqlalchemy import Column, String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import UUIDMixin, TimestampMixin
from app.database import Base


class UsageEvent(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "usage_events"

    tenant_id = Column(UUID(as_uuid=True),
                       ForeignKey("tenants.id", ondelete="CASCADE"),
                       nullable=False)
    user_id = Column(UUID(as_uuid=True),
                     ForeignKey("users.id", ondelete="SET NULL"),
                     nullable=True)
    event_type = Column(String(50), nullable=False)  # e.g. "ask"

    __table_args__ = (
        Index("ix_usage_tenant_type_created",
              "tenant_id", "event_type", "created_at"),
    )
