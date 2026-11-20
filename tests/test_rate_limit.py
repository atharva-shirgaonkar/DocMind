from unittest.mock import AsyncMock, patch
import pytest
import redis.asyncio as aioredis
from httpx import AsyncClient, ASGITransport
from app.config import get_settings
from app.main import app
from tests.conftest import auth_headers


async def _flush_rate_limit_keys():
    client = aioredis.from_url(get_settings().redis_url)
    try:
        keys = [key async for key in client.scan_iter(match="rl:*")]
        if keys:
            await client.delete(*keys)
    finally:
        await client.aclose()


@pytest.mark.ratelimit
@pytest.mark.asyncio
async def test_auth_rate_limit_returns_429_after_limit():
    await _flush_rate_limit_keys()
    settings = get_settings()
    original_limit = settings.auth_rate_limit_per_minute
    settings.auth_rate_limit_per_minute = 3
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            responses = [
                await client.post(
                    "/api/v1/auth/login",
                    data={"username": "missing@example.com", "password": "wrong"},
                )
                for _ in range(4)
            ]
    finally:
        settings.auth_rate_limit_per_minute = original_limit

    assert [r.status_code for r in responses] == [401, 401, 401, 429]
    assert "Retry-After" in responses[3].headers


@pytest.mark.ratelimit
@pytest.mark.asyncio
async def test_query_rate_limit_applies_to_search():
    await _flush_rate_limit_keys()
    settings = get_settings()
    original_limit = settings.query_rate_limit_per_minute
    settings.query_rate_limit_per_minute = 2
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            headers = await auth_headers(client, "Rate Limit Search Org")
            with (
                patch(
                    "app.services.rag.generate_chat",
                    new=AsyncMock(return_value="Mock answer [1]."),
                ),
                patch("app.api.search.hybrid_search_chunks", new=AsyncMock(return_value=[])),
            ):
                responses = [
                    await client.post(
                        "/api/v1/search",
                        json={"query": "rate limit test"},
                        headers=headers,
                    )
                    for _ in range(3)
                ]
    finally:
        settings.query_rate_limit_per_minute = original_limit

    assert [r.status_code for r in responses] == [200, 200, 429]


@pytest.mark.ratelimit
@pytest.mark.asyncio
async def test_rate_limiting_can_be_disabled():
    await _flush_rate_limit_keys()
    settings = get_settings()
    original_enabled = settings.rate_limit_enabled
    settings.rate_limit_enabled = False
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            responses = [
                await client.post(
                    "/api/v1/auth/login",
                    data={"username": "missing@example.com", "password": "wrong"},
                )
                for _ in range(20)
            ]
    finally:
        settings.rate_limit_enabled = original_enabled

    assert all(r.status_code == 401 for r in responses)
    assert all(r.status_code != 429 for r in responses)
