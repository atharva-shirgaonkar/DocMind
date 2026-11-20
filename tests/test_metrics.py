import uuid
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import AsyncSessionLocal
from app.models.document import Document, DocumentStatus, DocumentType
from tests.conftest import auth_headers


async def _tenant_id(client, headers):
    response = await client.get("/api/v1/auth/me", headers=headers)
    return uuid.UUID(response.json()["tenant_id"])


async def _insert_document(db, tenant_id, status):
    document = Document(
        tenant_id=tenant_id,
        filename=f"{uuid.uuid4().hex}.pdf",
        original_filename="metrics.pdf",
        file_type=DocumentType.PDF,
        file_size_bytes=100,
        storage_path="/tmp/metrics.pdf",
        status=status,
    )
    db.add(document)


@pytest.mark.asyncio
async def test_new_tenant_has_empty_usage_metrics():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await auth_headers(client, f"Empty {uuid.uuid4().hex[:6]}")
        response = await client.get("/api/v1/metrics/usage", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["documents_by_status"] == {
        "pending": 0, "processing": 0, "ready": 0, "failed": 0,
    }
    assert data["total_documents"] == 0
    assert data["total_chunks"] == 0
    assert data["queries_last_24h"] == 0
    assert data["queries_remaining"] == data["daily_query_limit"]
    assert data["avg_latency_ms"] is None


@pytest.mark.asyncio
async def test_metrics_count_documents_by_status():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await auth_headers(client, f"Counts {uuid.uuid4().hex[:6]}")
        tenant_id = await _tenant_id(client, headers)
        async with AsyncSessionLocal() as db:
            await _insert_document(db, tenant_id, DocumentStatus.READY)
            await _insert_document(db, tenant_id, DocumentStatus.READY)
            await _insert_document(db, tenant_id, DocumentStatus.FAILED)
            await db.commit()

        response = await client.get("/api/v1/metrics/usage", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["documents_by_status"] == {
        "pending": 0, "processing": 0, "ready": 2, "failed": 1,
    }
    assert data["total_documents"] == 3


@pytest.mark.asyncio
async def test_ask_updates_query_count_and_average_latency():
    mock_chunks = [{
        "chunk_id": uuid.uuid4(),
        "document_id": uuid.uuid4(),
        "document_name": "metrics.pdf",
        "page_number": 1,
        "chunk_index": 0,
        "content": "Some answer context",
        "score": 0.9,
    }]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await auth_headers(client, f"Queries {uuid.uuid4().hex[:6]}")
        with (
            patch(
                "app.services.rag.generate_chat",
                new=AsyncMock(return_value="Mock answer [1]."),
            ),
            patch("app.services.rag.search_chunks", new=AsyncMock(return_value=mock_chunks)),
        ):
            first = await client.post(
                "/api/v1/ask", json={"question": "question one"}, headers=headers
            )
            second = await client.post(
                "/api/v1/ask", json={"question": "question two"}, headers=headers
            )
        metrics = await client.get("/api/v1/metrics/usage", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    data = metrics.json()
    assert data["queries_last_24h"] == 2
    assert data["queries_remaining"] == data["daily_query_limit"] - 2
    assert isinstance(data["avg_latency_ms"], (int, float))


@pytest.mark.asyncio
async def test_metrics_are_tenant_scoped():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers_a = await auth_headers(client, f"Tenant A {uuid.uuid4().hex[:6]}")
        headers_b = await auth_headers(client, f"Tenant B {uuid.uuid4().hex[:6]}")
        tenant_a_id = await _tenant_id(client, headers_a)
        async with AsyncSessionLocal() as db:
            await _insert_document(db, tenant_a_id, DocumentStatus.READY)
            await db.commit()

        metrics_b = await client.get("/api/v1/metrics/usage", headers=headers_b)

    assert metrics_b.status_code == 200
    assert metrics_b.json()["total_documents"] == 0


@pytest.mark.asyncio
async def test_metrics_requires_authentication():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/metrics/usage")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_detailed_health_reports_worker_ping():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        with patch("app.api.health.celery_app.control.inspect") as inspect:
            inspect.return_value.ping.return_value = {"w1": {"ok": "pong"}}
            healthy = await client.get("/api/v1/health/detailed")

        with patch("app.api.health.celery_app.control.inspect") as inspect:
            inspect.return_value.ping.return_value = None
            no_worker = await client.get("/api/v1/health/detailed")

    healthy_data = healthy.json()
    assert healthy_data["checks"]["worker"]["status"] == "healthy"
    assert healthy_data["checks"]["worker"]["workers"] == 1
    assert no_worker.json()["checks"]["worker"] == {"status": "unhealthy"}
    assert no_worker.json()["status"] == "degraded"
