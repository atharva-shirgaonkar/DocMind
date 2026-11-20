import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import AsyncSessionLocal
from app.models.document import Document, DocumentStatus, DocumentType
from app.models.chunk import Chunk
from tests.conftest import auth_headers


async def _tenant_id(client, headers):
    response = await client.get("/api/v1/auth/me", headers=headers)
    return uuid.UUID(response.json()["tenant_id"])


async def _insert_document_with_chunks(tenant_id, chunk_values):
    async with AsyncSessionLocal() as db:
        document = Document(
            tenant_id=tenant_id,
            filename=f"{uuid.uuid4().hex}.pdf",
            original_filename="chunks.pdf",
            file_type=DocumentType.PDF,
            file_size_bytes=128,
            storage_path="/tmp/chunks.pdf",
            status=DocumentStatus.READY,
            chunk_count=len(chunk_values),
        )
        db.add(document)
        await db.flush()
        for index, content in chunk_values:
            db.add(Chunk(
                document_id=document.id,
                tenant_id=tenant_id,
                content=content,
                chunk_index=index,
                page_number=index + 1,
                embedding=[0.0] * 384,
            ))
        await db.commit()
        return document.id


@pytest.mark.asyncio
async def test_list_chunks_returns_ordered_items_without_embeddings():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await auth_headers(client, f"Chunks {uuid.uuid4().hex[:6]}")
        tenant_id = await _tenant_id(client, headers)
        document_id = await _insert_document_with_chunks(
            tenant_id, [(2, "third"), (0, "first"), (1, "second")]
        )
        response = await client.get(
            f"/api/v1/documents/{document_id}/chunks", headers=headers
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert [item["chunk_index"] for item in data["items"]] == [0, 1, 2]
    assert all("embedding" not in item for item in data["items"])


@pytest.mark.asyncio
async def test_chunk_pagination():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await auth_headers(client, f"Paging {uuid.uuid4().hex[:6]}")
        tenant_id = await _tenant_id(client, headers)
        document_id = await _insert_document_with_chunks(
            tenant_id, [(0, "zero"), (1, "one"), (2, "two")]
        )
        first_page = await client.get(
            f"/api/v1/documents/{document_id}/chunks?limit=2", headers=headers
        )
        second_page = await client.get(
            f"/api/v1/documents/{document_id}/chunks?limit=2&offset=2",
            headers=headers,
        )

    assert first_page.status_code == 200
    assert len(first_page.json()["items"]) == 2
    assert first_page.json()["total"] == 3
    assert second_page.status_code == 200
    assert len(second_page.json()["items"]) == 1
    assert second_page.json()["total"] == 3


@pytest.mark.asyncio
async def test_get_chunk_by_index_returns_content_and_char_count():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await auth_headers(client, f"Single {uuid.uuid4().hex[:6]}")
        tenant_id = await _tenant_id(client, headers)
        document_id = await _insert_document_with_chunks(
            tenant_id, [(0, "first passage"), (1, "second passage")]
        )
        response = await client.get(
            f"/api/v1/documents/{document_id}/chunks/1", headers=headers
        )

    assert response.status_code == 200
    assert response.json()["content"] == "second passage"
    assert response.json()["char_count"] == len("second passage")


@pytest.mark.asyncio
async def test_unknown_chunk_index_returns_404():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await auth_headers(client, f"Missing {uuid.uuid4().hex[:6]}")
        tenant_id = await _tenant_id(client, headers)
        document_id = await _insert_document_with_chunks(tenant_id, [(0, "only")])
        response = await client.get(
            f"/api/v1/documents/{document_id}/chunks/99", headers=headers
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Chunk not found."


@pytest.mark.asyncio
async def test_tenant_cannot_list_or_read_other_tenant_chunks():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers_a = await auth_headers(client, f"Tenant A {uuid.uuid4().hex[:6]}")
        headers_b = await auth_headers(client, f"Tenant B {uuid.uuid4().hex[:6]}")
        tenant_a = await _tenant_id(client, headers_a)
        document_id = await _insert_document_with_chunks(tenant_a, [(0, "private")])
        list_response = await client.get(
            f"/api/v1/documents/{document_id}/chunks", headers=headers_b
        )
        item_response = await client.get(
            f"/api/v1/documents/{document_id}/chunks/0", headers=headers_b
        )

    assert list_response.status_code == 404
    assert item_response.status_code == 404
    assert list_response.json()["detail"] == "Document not found."
    assert item_response.json()["detail"] == "Document not found."


@pytest.mark.asyncio
async def test_chunk_routes_require_authentication():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        document_id = uuid.uuid4()
        list_response = await client.get(
            f"/api/v1/documents/{document_id}/chunks"
        )
        item_response = await client.get(
            f"/api/v1/documents/{document_id}/chunks/0"
        )

    assert list_response.status_code == 401
    assert item_response.status_code == 401
