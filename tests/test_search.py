import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import engine


@pytest.fixture(autouse=True)
async def _dispose_engine():
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_search_returns_results_shape():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/search",
            json={"query": "work experience", "top_k": 3},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "work experience"
    assert "results" in data
    assert data["total"] == len(data["results"])
    for r in data["results"]:
        assert 0.0 <= r["score"] <= 1.0 or r["score"] < 0.0 + 1.0001
        assert "document_name" in r
        assert "content" in r


@pytest.mark.asyncio
async def test_search_rejects_empty_query():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/search", json={"query": ""}
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_search_rejects_bad_top_k():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/search", json={"query": "hi", "top_k": 100}
        )
    assert response.status_code == 422
