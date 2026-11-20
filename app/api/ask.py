from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
import time
from app.database import get_db
from app.core.rate_limit import user_rate_limit
from app.models.user import User
from app.schemas.ask import AskRequest, AskResponse
from app.services.rag import answer_question
from app.services.quota import check_and_record_query
from app.models.query_log import QueryLog

router = APIRouter(prefix="/ask", tags=["Ask"])


@router.post("", response_model=AskResponse)
async def ask(
    body: AskRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(user_rate_limit()),
):
    """Answer a question from the tenant's documents, with citations."""
    await check_and_record_query(db, user.tenant_id, user.id)
    started_at = time.perf_counter()
    result = await answer_question(
        db=db,
        tenant_id=user.tenant_id,
        question=body.question,
        top_k=body.top_k,
        document_id=body.document_id,
    )
    elapsed_ms = int((time.perf_counter() - started_at) * 1000)
    try:
        db.add(QueryLog(
            tenant_id=user.tenant_id,
            user_id=user.id,
            question=body.question,
            answer=result["answer"],
            sources=jsonable_encoder(result["sources"]),
            latency_ms=elapsed_ms,
        ))
        await db.commit()
    except Exception:
        await db.rollback()
    return AskResponse(**result)
