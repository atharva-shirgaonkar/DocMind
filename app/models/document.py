from sqlalchemy import Column, String, Integer, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum
from app.models.base import UUIDMixin, TimestampMixin
from app.database import Base


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"       # Uploaded, not yet processed
    PROCESSING = "processing" # Celery worker picked it up
    READY = "ready"           # Chunked + embedded, queryable
    FAILED = "failed"         # Processing error


class DocumentType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"


class Document(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    tenant_id = Column(UUID(as_uuid=True),
                       ForeignKey("tenants.id", ondelete="CASCADE"),
                       nullable=False, index=True)
    uploaded_by_id = Column(UUID(as_uuid=True),
                            ForeignKey("users.id", ondelete="SET NULL"),
                            nullable=True)

    # File metadata
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_type = Column(Enum(DocumentType), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    storage_path = Column(String(1000), nullable=False)

    # Processing state
    status = Column(Enum(DocumentStatus),
                    default=DocumentStatus.PENDING, nullable=False, index=True)
    chunk_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)

    # Optional metadata (title, author, page count, etc.)
    doc_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="documents")
    uploaded_by = relationship("User", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document",
                          cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document filename={self.original_filename} status={self.status}>"
