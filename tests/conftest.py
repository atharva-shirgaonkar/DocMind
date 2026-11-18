import uuid
import pytest_asyncio
from app.database import engine


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine():
    await engine.dispose()
    yield
    await engine.dispose()


async def auth_headers(client, tenant_name="Test Org"):
    email = f"u-{uuid.uuid4().hex[:8]}@example.com"
    r = await client.post("/api/v1/auth/register", json={
        "tenant_name": tenant_name, "email": email,
        "password": "StrongPass123",
    })
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
