from sqlalchemy import Column, Text, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import UUIDMixin, TimestampMixin
from app.database import Base


class QueryLog(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "query_logs"

    tenant_id = Column(UUID(as_uuid=True),
                       ForeignKey("tenants.id", ondelete="CASCADE"),
                       nullable=False)
    user_id = Column(UUID(as_uuid=True),
                     ForeignKey("users.id", ondelete="SET NULL"),
                     nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(JSONB, nullable=False, default=list)
    latency_ms = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("ix_query_logs_tenant_created", "tenant_id", "created_at"),
    )
