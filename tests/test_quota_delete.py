import io
import uuid
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import AsyncSessionLocal
from app.models.tenant import Tenant
from tests.conftest import auth_headers


def _pdf_file():
    return {"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 quota delete test"), "application/pdf")}


@pytest.mark.asyncio
async def test_upload_delete_then_get_returns_404():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await auth_headers(client)
        upload = await client.post(
            "/api/v1/documents/upload", files=_pdf_file(), headers=headers
        )
        assert upload.status_code == 201
        document_id = upload.json()["id"]

        deleted = await client.delete(
            f"/api/v1/documents/{document_id}", headers=headers
        )
        fetched = await client.get(
            f"/api/v1/documents/{document_id}", headers=headers
        )

    assert deleted.status_code == 204
    assert fetched.status_code == 404


@pytest.mark.asyncio
async def test_tenant_cannot_delete_another_tenants_document():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers_a = await auth_headers(client, f"Tenant A {uuid.uuid4().hex[:6]}")
        headers_b = await auth_headers(client, f"Tenant B {uuid.uuid4().hex[:6]}")
        upload = await client.post(
            "/api/v1/documents/upload", files=_pdf_file(), headers=headers_a
        )
        document_id = upload.json()["id"]

        deleted = await client.delete(
            f"/api/v1/documents/{document_id}", headers=headers_b
        )
        still_exists = await client.get(
            f"/api/v1/documents/{document_id}", headers=headers_a
        )

    assert upload.status_code == 201
    assert deleted.status_code == 404
    assert still_exists.status_code == 200


@pytest.mark.asyncio
async def test_daily_query_quota_blocks_third_ask():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await auth_headers(client, f"Quota Tenant {uuid.uuid4().hex[:6]}")
        me = await client.get("/api/v1/auth/me", headers=headers)
        tenant_id = uuid.UUID(me.json()["tenant_id"])

        async with AsyncSessionLocal() as db:
            tenant = await db.get(Tenant, tenant_id)
            tenant.max_queries_per_day = 2
            await db.commit()

        with patch(
            "app.services.rag.generate_chat",
            new=AsyncMock(return_value="Mock answer [1]."),
        ):
            first = await client.post(
                "/api/v1/ask", json={"question": "first"}, headers=headers
            )
            second = await client.post(
                "/api/v1/ask", json={"question": "second"}, headers=headers
            )
            third = await client.post(
                "/api/v1/ask", json={"question": "third"}, headers=headers
            )

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429


@pytest.mark.asyncio
async def test_delete_requires_authentication():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete(
            f"/api/v1/documents/{uuid.uuid4()}"
        )

    assert response.status_code == 401
