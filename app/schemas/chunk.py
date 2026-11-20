from uuid import UUID
from pydantic import BaseModel


class ChunkItem(BaseModel):
    id: UUID
    chunk_index: int
    page_number: int | None
    content: str
    char_count: int


class ChunkListResponse(BaseModel):
    document_id: UUID
    items: list[ChunkItem]
    total: int
