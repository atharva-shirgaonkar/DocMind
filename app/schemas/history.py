from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class HistoryItem(BaseModel):
    id: UUID
    question: str
    answer: str
    latency_ms: int
    created_at: datetime
    user_id: UUID | None
    model_config = {"from_attributes": True}


class HistoryDetail(HistoryItem):
    sources: list[dict]


class HistoryListResponse(BaseModel):
    items: list[HistoryItem]
    total: int
