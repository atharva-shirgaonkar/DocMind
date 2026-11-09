from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.documents import get_or_create_dev_tenant
from app.schemas.search import SearchRequest, SearchResponse, SearchResult
from app.services.search import search_chunks

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
async def search(
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """Semantic search across the current tenant's READY documents."""
    tenant = await get_or_create_dev_tenant(db)
    rows = await search_chunks(
        db=db,
        tenant_id=tenant.id,
        query=body.query,
        top_k=body.top_k,
        document_id=body.document_id,
    )
    return SearchResponse(
        query=body.query,
        results=[SearchResult(**r) for r in rows],
        total=len(rows),
    )
