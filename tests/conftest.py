import uuid
import pytest
import pytest_asyncio
from app.config import get_settings
from app.database import engine


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine():
    await engine.dispose()
    yield
    await engine.dispose()


@pytest.fixture(autouse=True)
def mock_query_embedding(request, monkeypatch):
    if request.node.get_closest_marker("realembed") is not None:
        return
    monkeypatch.setattr(
        "app.services.search.embed_query",
        lambda query: [0.1] * 384,
    )


@pytest.fixture(autouse=True)
def disable_rate_limit_unless_marked(request):
    settings = get_settings()
    original = settings.rate_limit_enabled
    if request.node.get_closest_marker("ratelimit") is None:
        settings.rate_limit_enabled = False
    yield
    settings.rate_limit_enabled = original


async def auth_headers(client, tenant_name="Test Org"):
    email = f"u-{uuid.uuid4().hex[:8]}@example.com"
    r = await client.post("/api/v1/auth/register", json={
        "tenant_name": tenant_name, "email": email,
        "password": "StrongPass123",
    })
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
