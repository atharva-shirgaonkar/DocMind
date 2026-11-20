from uuid import UUID
from sqlalchemy import select, func
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


async def keyword_search_chunks(
    db,
    tenant_id,
    query,
    top_k=5,
    document_id=None,
) -> list[dict]:
    tsv = func.to_tsvector("english", Chunk.content)
    tsq = func.websearch_to_tsquery("english", query)
    rank = func.ts_rank_cd(tsv, tsq)

    stmt = (
        select(
            Chunk.id,
            Chunk.document_id,
            Chunk.page_number,
            Chunk.chunk_index,
            Chunk.content,
            Document.original_filename,
            rank.label("score"),
        )
        .join(Document, Document.id == Chunk.document_id)
        .where(
            Chunk.tenant_id == tenant_id,
            Document.status == DocumentStatus.READY,
            tsv.op("@@")(tsq),
        )
        .order_by(rank.desc())
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


def reciprocal_rank_fusion(
    rankings: list[list[dict]], k: int = 60, top_k: int = 5
) -> list[dict]:
    fused_scores: dict[object, float] = {}
    first_results: dict[object, dict] = {}

    for ranking in rankings:
        for rank, result in enumerate(ranking, start=1):
            chunk_id = result["chunk_id"]
            first_results.setdefault(chunk_id, dict(result))
            fused_scores[chunk_id] = fused_scores.get(chunk_id, 0.0) + 1 / (k + rank)

    ordered_ids = sorted(
        fused_scores,
        key=lambda chunk_id: fused_scores[chunk_id],
        reverse=True,
    )[:top_k]
    fused = []
    for chunk_id in ordered_ids:
        result = first_results[chunk_id]
        result["score"] = round(fused_scores[chunk_id], 6)
        fused.append(result)
    return fused


async def hybrid_search_chunks(
    db,
    tenant_id,
    query,
    top_k=5,
    document_id=None,
    mode="hybrid",
):
    if mode == "vector":
        return await search_chunks(
            db=db,
            tenant_id=tenant_id,
            query=query,
            top_k=top_k,
            document_id=document_id,
        )
    if mode == "keyword":
        return await keyword_search_chunks(
            db=db,
            tenant_id=tenant_id,
            query=query,
            top_k=top_k,
            document_id=document_id,
        )
    if mode == "hybrid":
        vector_results = await search_chunks(
            db=db,
            tenant_id=tenant_id,
            query=query,
            top_k=top_k * 3,
            document_id=document_id,
        )
        keyword_results = await keyword_search_chunks(
            db=db,
            tenant_id=tenant_id,
            query=query,
            top_k=top_k * 3,
            document_id=document_id,
        )
        return reciprocal_rank_fusion(
            [vector_results, keyword_results], top_k=top_k
        )
    raise ValueError(f"Unsupported search mode: {mode}")
