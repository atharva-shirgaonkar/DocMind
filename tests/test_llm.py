from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import HTTPException

from app.config import get_settings
from app.services.llm import generate_chat


def _mock_async_client(response=None, error=None):
    client = AsyncMock()
    client.__aenter__.return_value = client
    client.__aexit__.return_value = False
    if error is not None:
        client.post.side_effect = error
    else:
        client.post.return_value = response
    return client


@pytest.mark.asyncio
async def test_generate_chat_returns_trimmed_provider_content():
    response = type("Response", (), {
        "status_code": 200,
        "json": lambda self: {"choices": [{"message": {"content": " hello "}}]},
        "text": "",
    })()
    client = _mock_async_client(response=response)

    with patch("app.services.llm.httpx.AsyncClient", return_value=client):
        assert await generate_chat([{"role": "user", "content": "Hi"}]) == "hello"


@pytest.mark.asyncio
async def test_generate_chat_requires_groq_key():
    settings = get_settings()
    original = settings.groq_api_key
    settings.groq_api_key = ""
    try:
        with pytest.raises(HTTPException) as exc:
            await generate_chat([])
        assert exc.value.status_code == 503
    finally:
        settings.groq_api_key = original


@pytest.mark.asyncio
async def test_generate_chat_maps_provider_error_to_502():
    response = type("Response", (), {"status_code": 500, "text": "provider error"})()
    client = _mock_async_client(response=response)

    with patch("app.services.llm.httpx.AsyncClient", return_value=client):
        with pytest.raises(HTTPException) as exc:
            await generate_chat([])
    assert exc.value.status_code == 502


@pytest.mark.asyncio
async def test_generate_chat_maps_network_error_to_502():
    client = _mock_async_client(error=httpx.ConnectError("network failure"))

    with patch("app.services.llm.httpx.AsyncClient", return_value=client):
        with pytest.raises(HTTPException) as exc:
            await generate_chat([])
    assert exc.value.status_code == 502
