from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from app.models.document import DocumentStatus, DocumentType


class DocumentUploadResponse(BaseModel):
    id: UUID
    filename: str
    original_filename: str
    file_type: DocumentType
    file_size_bytes: int
    status: DocumentStatus
    created_at: datetime
    message: str

    model_config = {"from_attributes": True}


class DocumentListItem(BaseModel):
    id: UUID
    original_filename: str
    file_type: DocumentType
    file_size_bytes: int
    status: DocumentStatus
    chunk_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    documents: list[DocumentListItem]
    total: int
