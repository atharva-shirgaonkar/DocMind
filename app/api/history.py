from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.database import get_db
from app.models.query_log import QueryLog
from app.models.user import User, UserRole
from app.schemas.history import HistoryDetail, HistoryListResponse

router = APIRouter(prefix="/history", tags=["History"])


def _visible_query(user: User):
    query = select(QueryLog).where(QueryLog.tenant_id == user.tenant_id)
    if user.role not in (UserRole.OWNER, UserRole.ADMIN):
        query = query.where(QueryLog.user_id == user.id)
    return query


@router.get("", response_model=HistoryListResponse)
async def list_history(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    visible_query = _visible_query(user)
    total = (await db.execute(
        select(func.count()).select_from(visible_query.subquery())
    )).scalar_one()
    rows = (await db.execute(
        visible_query.order_by(QueryLog.created_at.desc())
        .limit(limit).offset(offset)
    )).scalars().all()
    return HistoryListResponse(items=rows, total=total)


@router.get("/{log_id}", response_model=HistoryDetail)
async def get_history_item(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        _visible_query(user).where(QueryLog.id == log_id)
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(status_code=404, detail="History entry not found.")
    return entry


@router.delete("/{log_id}", status_code=204)
async def delete_history_item(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        _visible_query(user).where(QueryLog.id == log_id)
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(status_code=404, detail="History entry not found.")
    await db.delete(entry)
    await db.commit()
