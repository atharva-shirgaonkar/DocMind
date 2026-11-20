from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.database import get_db
from app.models.chunk import Chunk
from app.models.document import Document, DocumentStatus
from app.models.query_log import QueryLog
from app.models.tenant import Tenant
from app.models.usage import UsageEvent
from app.models.user import User
from app.schemas.metrics import UsageMetrics

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/usage", response_model=UsageMetrics)
async def usage_metrics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tenant_id = user.tenant_id
    since = datetime.utcnow() - timedelta(hours=24)

    document_rows = (await db.execute(
        select(Document.status, func.count(Document.id))
        .where(Document.tenant_id == tenant_id)
        .group_by(Document.status)
    )).all()
    documents_by_status = {status.value.lower(): 0 for status in DocumentStatus}
    for status, count in document_rows:
        documents_by_status[status.value.lower()] = count
    total_documents = sum(documents_by_status.values())

    total_chunks = (await db.execute(
        select(func.count(Chunk.id)).where(Chunk.tenant_id == tenant_id)
    )).scalar_one()

    queries_last_24h = (await db.execute(
        select(func.count(UsageEvent.id)).where(
            UsageEvent.tenant_id == tenant_id,
            UsageEvent.event_type == "ask",
            UsageEvent.created_at >= since,
        )
    )).scalar_one()

    tenant = (await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )).scalar_one()

    avg_latency = (await db.execute(
        select(func.avg(QueryLog.latency_ms)).where(
            QueryLog.tenant_id == tenant_id,
            QueryLog.created_at >= since,
        )
    )).scalar_one()

    return UsageMetrics(
        documents_by_status=documents_by_status,
        total_documents=total_documents,
        total_chunks=total_chunks,
        queries_last_24h=queries_last_24h,
        daily_query_limit=tenant.max_queries_per_day,
        queries_remaining=max(tenant.max_queries_per_day - queries_last_24h, 0),
        avg_latency_ms=round(float(avg_latency), 1) if avg_latency is not None else None,
    )
