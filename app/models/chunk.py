from sqlalchemy import Column, Integer, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.models.base import UUIDMixin, TimestampMixin
from app.database import Base

EMBEDDING_DIMENSIONS = 1536  # OpenAI text-embedding-3-small


class Chunk(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "chunks"

    document_id = Column(UUID(as_uuid=True),
                         ForeignKey("documents.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True),
                       ForeignKey("tenants.id", ondelete="CASCADE"),
                       nullable=False, index=True)

    # Content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Position in document

    # Source reference (for citations)
    page_number = Column(Integer, nullable=True)
    chunk_metadata = Column(JSONB, default=dict, nullable=False)

    # The embedding vector
    embedding = Column(Vector(EMBEDDING_DIMENSIONS), nullable=True)

    # Relationships
    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        # IVFFlat index for fast approximate nearest-neighbour search.
        # Created here but only becomes effective after VACUUM ANALYZE
        # once you have >1000 rows. Safe to include from the start.
        Index(
            "ix_chunks_embedding_ivfflat",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    def __repr__(self):
        return f"<Chunk doc={self.document_id} index={self.chunk_index}>"
