import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.document import Document, DocumentStatus, DocumentType
from app.models.tenant import Tenant
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentListItem,
)
from app.services.storage import validate_file, save_upload
from app.workers.tasks import process_document

router = APIRouter(prefix="/documents", tags=["Documents"])


async def get_or_create_dev_tenant(db: AsyncSession) -> Tenant:
    """
    DEV SHORTCUT — Phase 3 replaces this with real JWT auth.
    Returns the first tenant, or creates a default one if none exists.
    """
    result = await db.execute(select(Tenant).limit(1))
    tenant = result.scalar_one_or_none()
    if not tenant:
        tenant = Tenant(
            name="Default Tenant",
            slug="default",
        )
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)
    return tenant


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a PDF or DOCX file.
    Creates a Document record with status PENDING.
    Processing (chunking + embedding) is triggered separately.
    """
    # 1. Validate file type
    file_type_str = validate_file(file)
    file_type = DocumentType(file_type_str)

    # 2. Resolve tenant (dev shortcut — real auth in Task 9)
    tenant = await get_or_create_dev_tenant(db)

    # 3. Check tenant document quota
    count_result = await db.execute(
        select(func.count(Document.id)).where(
            Document.tenant_id == tenant.id
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
    storage_path, safe_name, file_size = await save_upload(
        file, str(tenant.id)
    )

    # 5. Create Document record
    document = Document(
        tenant_id=tenant.id,
        filename=safe_name,
        original_filename=file.filename or safe_name,
        file_type=file_type,
        file_size_bytes=file_size,
        storage_path=storage_path,
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
    status: DocumentStatus | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List all documents for the current tenant."""
    tenant = await get_or_create_dev_tenant(db)

    query = select(Document).where(Document.tenant_id == tenant.id)
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
):
    """Get a single document by ID."""
    tenant = await get_or_create_dev_tenant(db)

    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.tenant_id == tenant.id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return DocumentListItem.model_validate(doc)
