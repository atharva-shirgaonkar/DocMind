from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.ask import AskRequest, AskResponse
from app.services.rag import answer_question

router = APIRouter(prefix="/ask", tags=["Ask"])


@router.post("", response_model=AskResponse)
async def ask(
    body: AskRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Answer a question from the tenant's documents, with citations."""
    result = await answer_question(
        db=db,
        tenant_id=user.tenant_id,
        question=body.question,
        top_k=body.top_k,
        document_id=body.document_id,
    )
    return AskResponse(**result)
