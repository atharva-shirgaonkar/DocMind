import json
import logging
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_response_contains_request_id():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")


@pytest.mark.asyncio
async def test_client_request_id_is_echoed():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/health", headers={"X-Request-ID": "abc-123"}
        )

    assert response.headers["X-Request-ID"] == "abc-123"


@pytest.mark.asyncio
async def test_requests_without_ids_get_unique_ids():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        first = await client.get("/api/v1/health")
        second = await client.get("/api/v1/health")

    assert first.headers["X-Request-ID"] != second.headers["X-Request-ID"]


@pytest.mark.asyncio
async def test_access_log_is_json_with_request_fields(caplog):
    logger = logging.getLogger("docmind.access")
    old_propagate = logger.propagate
    logger.propagate = True
    try:
        with caplog.at_level(logging.INFO, logger="docmind.access"):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                await client.get("/api/v1/health")
    finally:
        logger.propagate = old_propagate

    records = [r for r in caplog.records if r.name == "docmind.access"]
    assert len(records) == 1
    event = json.loads(records[0].getMessage())
    assert event["request_id"]
    assert event["method"] == "GET"
    assert event["path"] == "/api/v1/health"
    assert event["status"] == 200
    assert isinstance(event["duration_ms"], (int, float))


@pytest.mark.asyncio
async def test_cors_preflight_allows_configured_origin():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


@pytest.mark.asyncio
async def test_cors_does_not_allow_unconfigured_origin():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/health", headers={"Origin": "http://evil.example"}
        )

    assert "access-control-allow-origin" not in response.headers
