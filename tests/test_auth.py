import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import engine


@pytest.fixture(autouse=True)
async def _dispose_engine():
    yield
    await engine.dispose()


def _creds():
    return f"user-{uuid.uuid4().hex[:8]}@example.com", "StrongPass123"


async def _register(client, email, password):
    return await client.post("/api/v1/auth/register", json={
        "tenant_name": "Test Org", "email": email, "password": password,
    })


@pytest.mark.asyncio
async def test_register_and_me():
    email, pw = _creds()
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url="http://test") as c:
        r = await _register(c, email, pw)
        assert r.status_code == 201
        token = r.json()["access_token"]
        me = await c.get("/api/v1/auth/me",
                         headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == email
    assert me.json()["role"] == "owner"


@pytest.mark.asyncio
async def test_duplicate_email_rejected():
    email, pw = _creds()
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url="http://test") as c:
        await _register(c, email, pw)
        r = await _register(c, email, pw)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_login_success_and_wrong_password():
    email, pw = _creds()
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url="http://test") as c:
        await _register(c, email, pw)
        ok = await c.post("/api/v1/auth/login",
                          data={"username": email, "password": pw})
        bad = await c.post("/api/v1/auth/login",
                           data={"username": email, "password": "wrongpass1"})
    assert ok.status_code == 200
    assert "access_token" in ok.json()
    assert bad.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_valid_token():
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url="http://test") as c:
        no_token = await c.get("/api/v1/auth/me")
        bad_token = await c.get("/api/v1/auth/me",
                                headers={"Authorization": "Bearer garbage"})
    assert no_token.status_code == 401
    assert bad_token.status_code == 401
