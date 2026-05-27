"""
Celery task: process_document

Flow:
  1. Load Document from DB → set status = PROCESSING
  2. Extract text from file
  3. Chunk the text
  4. Embed the chunks (OpenAI)
  5. Bulk-insert Chunk rows
  6. Set status = READY, chunk_count = len(chunks)

On any exception: set status = FAILED, store error_message.
"""
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.workers import celery_app
from app.config import get_settings
from app.models.document import Document, DocumentStatus
from app.models.chunk import Chunk
from app.services.extractor import extract_text
from app.services.chunker import chunk_pages
from app.services.embedder import embed_chunks

settings = get_settings()

# Celery workers run synchronously — we need a dedicated async engine
_engine = create_async_engine(settings.database_url, pool_pre_ping=True)
_SessionLocal = sessionmaker(_engine, class_=AsyncSession,
                              expire_on_commit=False)


async def _process(document_id: str) -> None:
    async with _SessionLocal() as db:
        # 1. Fetch document
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        # 2. Mark as PROCESSING
        doc.status = DocumentStatus.PROCESSING
        await db.commit()

        try:
            # 3. Extract text
            pages = extract_text(doc.storage_path, doc.file_type.value)
            if not pages:
                raise ValueError("No extractable text found in document.")

            # 4. Chunk
            raw_chunks = chunk_pages(pages)
            if not raw_chunks:
                raise ValueError("Document produced zero chunks after splitting.")

            # 5. Embed
            enriched = embed_chunks(raw_chunks)

            # 6. Persist chunks
            chunk_objs = [
                Chunk(
                    document_id=doc.id,
                    tenant_id=doc.tenant_id,
                    content=c["content"],
                    chunk_index=c["chunk_index"],
                    page_number=c.get("page_number"),
                    embedding=c["embedding"],
                    chunk_metadata={
                        "char_count": c.get("char_count", 0),
                    },
                )
                for c in enriched
            ]
            db.add_all(chunk_objs)

            # 7. Update document
            doc.status = DocumentStatus.READY
            doc.chunk_count = len(chunk_objs)
            await db.commit()

        except Exception as e:
            await db.rollback()
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)[:1000]
            await db.commit()
            raise


@celery_app.task(name="process_document", bind=True, max_retries=0)
def process_document(self, document_id: str) -> dict:
    """
    Entry point called by Celery.
    Wraps the async pipeline in a synchronous runner.
    """
    asyncio.run(_process(document_id))
    return {"document_id": document_id, "status": "processed"}
