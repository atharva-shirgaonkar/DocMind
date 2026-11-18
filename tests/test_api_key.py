import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_api_key_authenticates_and_can_be_revoked():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        jwt_headers = await auth_headers(client)

        created = await client.post(
            "/api/v1/auth/api-key", headers=jwt_headers
        )
        assert created.status_code == 201
        key_data = created.json()
        api_key = key_data["api_key"]
        assert api_key.startswith("dm_")
        assert key_data["note"] == "Store this key now. It will not be shown again."

        api_key_headers = {"X-API-Key": api_key}
        me = await client.get("/api/v1/auth/me", headers=api_key_headers)
        assert me.status_code == 200

        revoked = await client.delete(
            "/api/v1/auth/api-key", headers=jwt_headers
        )
        assert revoked.status_code == 204

        rejected = await client.get("/api/v1/auth/me", headers=api_key_headers)
        assert rejected.status_code == 401
        assert rejected.json()["detail"] == "Invalid API key."


@pytest.mark.asyncio
async def test_invalid_api_key_does_not_fall_back_to_valid_jwt():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        jwt_headers = await auth_headers(client)
        response = await client.get(
            "/api/v1/auth/me",
            headers={**jwt_headers, "X-API-Key": "dm-invalid"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key."
