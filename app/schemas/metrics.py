from pydantic import BaseModel


class UsageMetrics(BaseModel):
    documents_by_status: dict[str, int]
    total_documents: int
    total_chunks: int
    queries_last_24h: int
    daily_query_limit: int
    queries_remaining: int
    avg_latency_ms: float | None
