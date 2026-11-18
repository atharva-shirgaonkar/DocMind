from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tenant import Tenant
from app.models.usage import UsageEvent


async def check_and_record_query(
    db: AsyncSession, tenant_id, user_id, event_type: str = "ask"
) -> None:
    """Raise 429 if the tenant hit its daily limit; else record usage."""
    tenant = (await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )).scalar_one()

    since = datetime.utcnow() - timedelta(hours=24)
    used = (await db.execute(
        select(func.count(UsageEvent.id)).where(
            UsageEvent.tenant_id == tenant_id,
            UsageEvent.event_type == event_type,
            UsageEvent.created_at >= since,
        )
    )).scalar_one()

    if used >= tenant.max_queries_per_day:
        raise HTTPException(
            status_code=429,
            detail=f"Daily query limit reached "
                   f"({tenant.max_queries_per_day} per 24 hours).",
        )

    db.add(UsageEvent(tenant_id=tenant_id, user_id=user_id,
                      event_type=event_type))
    await db.commit()
