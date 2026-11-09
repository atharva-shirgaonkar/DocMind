from pydantic import BaseModel, Field
from uuid import UUID


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=20)
    document_id: UUID | None = None


class SearchResult(BaseModel):
    chunk_id: UUID
    document_id: UUID
    document_name: str
    page_number: int | None
    chunk_index: int
    content: str
    score: float   # cosine similarity, 0 to 1, higher is better


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int
