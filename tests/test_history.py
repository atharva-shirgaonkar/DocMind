import uuid
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import create_access_token
from tests.conftest import auth_headers


MOCK_CHUNKS = [{
    "chunk_id": uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
    "document_id": uuid.UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
    "document_name": "resume.pdf",
    "page_number": 1,
    "chunk_index": 0,
    "content": "Python, SQL and FastAPI experience.",
    "score": 0.8,
}]


def _mock_rag():
    return (
        patch("app.services.rag.search_chunks", new=AsyncMock(return_value=MOCK_CHUNKS)),
        patch("app.services.rag.generate_chat", new=AsyncMock(return_value="Python and SQL [1].")),
    )


async def _ask(client, headers, question="What skills are listed?"):
    with _mock_rag()[0], _mock_rag()[1]:
        return await client.post(
            "/api/v1/ask", json={"question": question}, headers=headers
        )


@pytest.mark.asyncio
async def test_ask_is_recorded_in_history():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await auth_headers(client, f"History {uuid.uuid4().hex[:6]}")
        asked = await _ask(client, headers)
        history = await client.get("/api/v1/history", headers=headers)

    assert asked.status_code == 200
    assert history.status_code == 200
    assert history.json()["total"] == 1
    assert history.json()["items"][0]["question"] == "What skills are listed?"


@pytest.mark.asyncio
async def test_history_detail_includes_sources():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await auth_headers(client, f"Detail {uuid.uuid4().hex[:6]}")
        await _ask(client, headers)
        history = await client.get("/api/v1/history", headers=headers)
        log_id = history.json()["items"][0]["id"]
        detail = await client.get(f"/api/v1/history/{log_id}", headers=headers)

    assert detail.status_code == 200
    assert isinstance(detail.json()["sources"], list)
    assert detail.json()["sources"]

