import uuid
import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.document import Document, DocumentStatus, DocumentType
from app.models.tenant import Tenant
from app.models.user import User
from app.api.deps import get_current_user
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentListItem,
)
from app.services.storage import validate_file, save_upload
from app.workers.tasks import process_document

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    response: Response,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Upload a PDF or DOCX file.
    Creates a Document record with status PENDING.
    Processing (chunking + embedding) is triggered separately.
    """
    # 1. Validate file type
    file_type_str = validate_file(file)
    file_type = DocumentType(file_type_str)

    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == user.tenant_id)
    )
    tenant = tenant_result.scalar_one()

    # 3. Check tenant document quota
    count_result = await db.execute(
        select(func.count(Document.id)).where(
            Document.tenant_id == user.tenant_id
        )
    )
    doc_count = count_result.scalar_one()
    if doc_count >= tenant.max_documents:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Tenant document quota reached "
                f"({tenant.max_documents} documents)."
            ),
        )

    # 4. Save file to disk
    storage_path, safe_name, file_size, content_hash = await save_upload(
        file, str(user.tenant_id)
    )

    duplicate_result = await db.execute(
        select(Document).where(
            Document.tenant_id == user.tenant_id,
            Document.content_hash == content_hash,
        )
    )
    existing = duplicate_result.scalar_one_or_none()
    if existing:
        os.remove(storage_path)
        response.status_code = 200
        return DocumentUploadResponse(
            id=existing.id,
            filename=existing.filename,
            original_filename=existing.original_filename,
            file_type=existing.file_type,
            file_size_bytes=existing.file_size_bytes,
            status=existing.status,
            created_at=existing.created_at,
            message="Duplicate file - existing document returned.",
        )

    # 5. Create Document record
    document = Document(
        tenant_id=user.tenant_id,
        uploaded_by_id=user.id,
        filename=safe_name,
        original_filename=file.filename or safe_name,
        file_type=file_type,
        file_size_bytes=file_size,
        storage_path=storage_path,
        content_hash=content_hash,
        status=DocumentStatus.PENDING,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Dispatch processing task to Celery worker
    process_document.delay(str(document.id))

    return DocumentUploadResponse(
        id=document.id,
        filename=document.filename,
        original_filename=document.original_filename,
        file_type=document.file_type,
        file_size_bytes=document.file_size_bytes,
        status=document.status,
        created_at=document.created_at,
        message="File uploaded successfully. Processing will begin shortly.",
    )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    status: DocumentStatus | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List all documents for the current tenant."""
    query = select(Document).where(Document.tenant_id == user.tenant_id)
    if status:
        query = query.where(Document.status == status)

    count_q = select(func.count()).select_from(
        query.subquery()
    )
    total = (await db.execute(count_q)).scalar_one()

    query = query.order_by(Document.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    docs = result.scalars().all()

    return DocumentListResponse(
        documents=[DocumentListItem.model_validate(d) for d in docs],
        total=total,
    )


@router.get("/{document_id}", response_model=DocumentListItem)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single document by ID."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.tenant_id == user.tenant_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return DocumentListItem.model_validate(doc)
