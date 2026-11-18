import io
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from tests.conftest import auth_headers


def _pdf_file():
    return {"file": ("same.pdf", io.BytesIO(b"%PDF-1.4 shared test bytes"), "application/pdf")}


@pytest.mark.asyncio
async def test_documents_are_isolated_and_deduped_per_tenant():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers_a = await auth_headers(client, tenant_name=f"Tenant A {uuid.uuid4().hex[:6]}")
        headers_b = await auth_headers(client, tenant_name=f"Tenant B {uuid.uuid4().hex[:6]}")

        upload_a = await client.post(
            "/api/v1/documents/upload", files=_pdf_file(), headers=headers_a
        )
        assert upload_a.status_code == 201
        document_a = upload_a.json()
        document_id_a = document_a["id"]

        other_tenant_document = await client.get(
            f"/api/v1/documents/{document_id_a}", headers=headers_b
        )
        assert other_tenant_document.status_code == 404

        list_b = await client.get("/api/v1/documents/", headers=headers_b)
        assert document_id_a not in [d["id"] for d in list_b.json()["documents"]]

        duplicate_a = await client.post(
            "/api/v1/documents/upload", files=_pdf_file(), headers=headers_a
        )
        assert duplicate_a.status_code == 200
        assert duplicate_a.json()["id"] == document_id_a

        list_a = await client.get("/api/v1/documents/", headers=headers_a)
        assert list_a.json()["total"] == 1

        upload_b = await client.post(
            "/api/v1/documents/upload", files=_pdf_file(), headers=headers_b
        )
        assert upload_b.status_code == 201
        assert upload_b.json()["id"] != document_id_a


@pytest.mark.asyncio
async def test_search_and_ask_require_authentication():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        search_response = await client.post(
            "/api/v1/search", json={"query": "private info"}
        )
        ask_response = await client.post(
            "/api/v1/ask", json={"question": "private info"}
        )

    assert search_response.status_code == 401
    assert ask_response.status_code == 401
