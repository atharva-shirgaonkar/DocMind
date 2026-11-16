from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.documents import get_or_create_dev_tenant
from app.schemas.ask import AskRequest, AskResponse
from app.services.rag import answer_question

router = APIRouter(prefix="/ask", tags=["Ask"])


@router.post("", response_model=AskResponse)
async def ask(
    body: AskRequest,
    db: AsyncSession = Depends(get_db),
):
    """Answer a question from the tenant's documents, with citations."""
    tenant = await get_or_create_dev_tenant(db)
    result = await answer_question(
        db=db,
        tenant_id=tenant.id,
        question=body.question,
        top_k=body.top_k,
        document_id=body.document_id,
    )
    return AskResponse(**result)
