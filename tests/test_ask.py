import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import engine
from app.services.rag import _dedupe


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine():
    await engine.dispose()
    yield
    await engine.dispose()


def test_dedupe_removes_identical_chunks():
    chunks = [
        {"content": "Same text here"},
        {"content": "same   text HERE"},
        {"content": "Different text"},
    ]
    assert len(_dedupe(chunks, 5)) == 2


def test_dedupe_respects_limit():
    chunks = [{"content": f"text {i}"} for i in range(10)]
    assert len(_dedupe(chunks, 3)) == 3


@pytest.mark.asyncio
async def test_ask_returns_answer_and_sources():
    with patch(
        "app.services.rag.generate_chat",
        new=AsyncMock(return_value="Mocked answer [1]."),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/ask",
                json={"question": "technical skills", "top_k": 3},
            )
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "technical skills"
    assert "answer" in data
    for s in data["sources"]:
        assert "citation_number" in s
        assert "document_name" in s


@pytest.mark.asyncio
async def test_ask_rejects_empty_question():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/ask", json={"question": ""}
        )
    assert response.status_code == 422
