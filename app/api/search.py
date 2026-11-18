from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.search import SearchRequest, SearchResponse, SearchResult
from app.services.search import search_chunks

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
async def search(
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Semantic search across the current tenant's READY documents."""
    rows = await search_chunks(
        db=db,
        tenant_id=user.tenant_id,
        query=body.query,
        top_k=body.top_k,
        document_id=body.document_id,
    )
    return SearchResponse(
        query=body.query,
        results=[SearchResult(**r) for r in rows],
        total=len(rows),
    )
