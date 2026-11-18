import uuid
import pytest
import pytest_asyncio
from app.config import get_settings
from app.database import engine


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine():
    await engine.dispose()


@pytest.fixture(autouse=True)
def disable_rate_limit_unless_marked(request):
    settings = get_settings()
    original = settings.rate_limit_enabled
    if request.node.get_closest_marker("ratelimit") is None:
        settings.rate_limit_enabled = False
    yield
    settings.rate_limit_enabled = original
    yield
    await engine.dispose()


async def auth_headers(client, tenant_name="Test Org"):
    email = f"u-{uuid.uuid4().hex[:8]}@example.com"
    r = await client.post("/api/v1/auth/register", json={
        "tenant_name": tenant_name, "email": email,
        "password": "StrongPass123",
    })
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
