from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chunk import Chunk
from app.models.document import Document, DocumentStatus
from app.services.embedder import get_model


def embed_query(query: str) -> list[float]:
    model = get_model()
    vector = next(iter(model.embed([query])))
    return vector.tolist()


async def search_chunks(
    db: AsyncSession,
    tenant_id: UUID,
    query: str,
    top_k: int = 5,
    document_id: UUID | None = None,
) -> list[dict]:
    query_vector = embed_query(query)

    distance = Chunk.embedding.cosine_distance(query_vector)

    stmt = (
        select(
            Chunk.id,
            Chunk.document_id,
            Chunk.page_number,
            Chunk.chunk_index,
            Chunk.content,
            Document.original_filename,
            (1 - distance).label("score"),
        )
        .join(Document, Document.id == Chunk.document_id)
        .where(
            Chunk.tenant_id == tenant_id,
            Document.status == DocumentStatus.READY,
            Chunk.embedding.is_not(None),
        )
        .order_by(distance)
        .limit(top_k)
    )
    if document_id:
        stmt = stmt.where(Chunk.document_id == document_id)

    rows = (await db.execute(stmt)).all()
    return [
        {
            "chunk_id": r.id,
            "document_id": r.document_id,
            "document_name": r.original_filename,
            "page_number": r.page_number,
            "chunk_index": r.chunk_index,
            "content": r.content,
            "score": float(r.score),
        }
        for r in rows
    ]
