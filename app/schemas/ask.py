from pydantic import BaseModel, Field
from uuid import UUID


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(4, ge=1, le=10)
    document_id: UUID | None = None


class AskSource(BaseModel):
    citation_number: int
    document_id: UUID
    document_name: str
    page_number: int | None
    chunk_index: int
    snippet: str
    score: float


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[AskSource]
