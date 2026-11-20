import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, func
from app.main import app
from app.database import AsyncSessionLocal
from app.models.chunk import Chunk
from app.models.document import Document, DocumentStatus, DocumentType
from tests.conftest import auth_headers


async def _register_tenant(client, name="Reprocess Org"):
    headers = await auth_headers(client, f"{name} {uuid.uuid4().hex[:6]}")
    me = await client.get("/api/v1/auth/me", headers=headers)
    return headers, uuid.UUID(me.json()["tenant_id"])


async def _insert_document(
    tenant_id,
    path,
    status=DocumentStatus.FAILED,
    updated_at=None,
    chunk_count=0,
):
    async with AsyncSessionLocal() as db:
        document = Document(
            tenant_id=tenant_id,
            filename=f"{uuid.uuid4().hex}.pdf",
            original_filename="test.pdf",
            file_type=DocumentType.PDF,
            file_size_bytes=32,
            storage_path=str(path),
            status=status,
            chunk_count=chunk_count,
            error_message="Previous processing failure",
            updated_at=updated_at or datetime.utcnow(),
        )
        db.add(document)
        await db.flush()
        for index in range(chunk_count):
            db.add(Chunk(
                document_id=document.id,
                tenant_id=tenant_id,
                content=f"Old chunk {index}",
                chunk_index=index,
                embedding=[0.0] * 384,
            ))
        await db.commit()
        return document.id


async def _chunk_count(document_id):
    async with AsyncSessionLocal() as db:
        return (await db.execute(
            select(func.count(Chunk.id)).where(Chunk.document_id == document_id)
        )).scalar_one()


@pytest.mark.asyncio
async def test_failed_document_reprocesses_and_dispatches(tmp_path):
    file_path = tmp_path / "failed.pdf"
    file_path.write_bytes(b"PDF source")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers, tenant_id = await _register_tenant(client)
        document_id = await _insert_document(tenant_id, file_path)

        with patch("app.api.documents.process_document", new=MagicMock()) as task:
            response = await client.post(
                f"/api/v1/documents/{document_id}/reprocess", headers=headers
            )
            task.delay.assert_called_once_with(str(document_id))

    assert response.status_code == 202
    assert response.json()["status"] == "pending"
    assert response.json()["chunk_count"] == 0
    assert response.json()["error_message"] is None


@pytest.mark.asyncio
async def test_ready_document_is_not_eligible(tmp_path):
    file_path = tmp_path / "ready.pdf"
    file_path.write_bytes(b"PDF source")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers, tenant_id = await _register_tenant(client)
        document_id = await _insert_document(
            tenant_id, file_path, status=DocumentStatus.READY
        )
        response = await client.post(
            f"/api/v1/documents/{document_id}/reprocess", headers=headers
        )

    assert response.status_code == 409
    assert response.json()["detail"] == "Document is not eligible for reprocessing."


@pytest.mark.asyncio
async def test_missing_source_file_keeps_document_failed(tmp_path):
    file_path = tmp_path / "missing.pdf"
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers, tenant_id = await _register_tenant(client)
        document_id = await _insert_document(tenant_id, file_path)
        with patch("app.api.documents.process_document", new=MagicMock()) as task:
            response = await client.post(
                f"/api/v1/documents/{document_id}/reprocess", headers=headers
            )
            task.delay.assert_not_called()

        async with AsyncSessionLocal() as db:
            document = await db.get(Document, document_id)

    assert response.status_code == 409
    assert document.status == DocumentStatus.FAILED
    assert document.error_message == "Source file missing. Please re-upload."


@pytest.mark.asyncio
async def test_other_tenant_cannot_reprocess_document(tmp_path):
    file_path = tmp_path / "tenant-a.pdf"
    file_path.write_bytes(b"PDF source")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers_a, tenant_a = await _register_tenant(client, "Tenant A")
        headers_b, tenant_b = await _register_tenant(client, "Tenant B")
        document_id = await _insert_document(tenant_a, file_path)
        response = await client.post(
            f"/api/v1/documents/{document_id}/reprocess", headers=headers_b
        )

    assert tenant_a != tenant_b
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."


@pytest.mark.asyncio
async def test_reprocess_requires_authentication():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            f"/api/v1/documents/{uuid.uuid4()}/reprocess"
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_stuck_processing_reprocesses_but_recent_processing_does_not(tmp_path):
    stuck_file = tmp_path / "stuck.pdf"
    recent_file = tmp_path / "recent.pdf"
    stuck_file.write_bytes(b"PDF source")
    recent_file.write_bytes(b"PDF source")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers, tenant_id = await _register_tenant(client)
        stuck_id = await _insert_document(
            tenant_id, stuck_file, status=DocumentStatus.PROCESSING,
            updated_at=datetime.utcnow() - timedelta(minutes=20),
        )
        recent_id = await _insert_document(
            tenant_id, recent_file, status=DocumentStatus.PROCESSING,
            updated_at=datetime.utcnow(),
        )
        with patch("app.api.documents.process_document", new=MagicMock()) as task:
            stuck_response = await client.post(
                f"/api/v1/documents/{stuck_id}/reprocess", headers=headers
            )
            task.delay.assert_called_once_with(str(stuck_id))
            task.reset_mock()
            recent_response = await client.post(
                f"/api/v1/documents/{recent_id}/reprocess", headers=headers
            )
            task.delay.assert_not_called()

    assert stuck_response.status_code == 202
    assert recent_response.status_code == 409


@pytest.mark.asyncio
async def test_reprocess_removes_existing_chunks(tmp_path):
    file_path = tmp_path / "chunked.pdf"
    file_path.write_bytes(b"PDF source")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers, tenant_id = await _register_tenant(client)
        document_id = await _insert_document(
            tenant_id, file_path, chunk_count=2
        )
        with patch("app.api.documents.process_document", new=MagicMock()):
            response = await client.post(
                f"/api/v1/documents/{document_id}/reprocess", headers=headers
            )

    assert response.status_code == 202
    assert await _chunk_count(document_id) == 0
