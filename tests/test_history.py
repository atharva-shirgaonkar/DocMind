import uuid
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import create_access_token
from tests.conftest import auth_headers


MOCK_CHUNKS = [{
    "chunk_id": uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
    "document_id": uuid.UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
    "document_name": "resume.pdf",
    "page_number": 1,
    "chunk_index": 0,
    "content": "Python, SQL and FastAPI experience.",
    "score": 0.8,
}]


def _mock_rag():
    return (
        patch("app.services.rag.search_chunks", new=AsyncMock(return_value=MOCK_CHUNKS)),
        patch("app.services.rag.generate_chat", new=AsyncMock(return_value="Python and SQL [1].")),
    )


async def _ask(client, headers, question="What skills are listed?"):
    with _mock_rag()[0], _mock_rag()[1]:
        return await client.post(
            "/api/v1/ask", json={"question": question}, headers=headers
        )


@pytest.mark.asyncio
async def test_ask_is_recorded_in_history():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await auth_headers(client, f"History {uuid.uuid4().hex[:6]}")
        asked = await _ask(client, headers)
        history = await client.get("/api/v1/history", headers=headers)

    assert asked.status_code == 200
    assert history.status_code == 200
    assert history.json()["total"] == 1
    assert history.json()["items"][0]["question"] == "What skills are listed?"


@pytest.mark.asyncio
async def test_history_detail_includes_sources():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await auth_headers(client, f"Detail {uuid.uuid4().hex[:6]}")
        await _ask(client, headers)
        history = await client.get("/api/v1/history", headers=headers)
        log_id = history.json()["items"][0]["id"]
        detail = await client.get(f"/api/v1/history/{log_id}", headers=headers)

    assert detail.status_code == 200
    assert isinstance(detail.json()["sources"], list)
    assert detail.json()["sources"]


@pytest.mark.asyncio
async def test_history_is_tenant_isolated_for_read_and_delete():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers_a = await auth_headers(client, f"Tenant A {uuid.uuid4().hex[:6]}")
        headers_b = await auth_headers(client, f"Tenant B {uuid.uuid4().hex[:6]}")
        await _ask(client, headers_a)
        history_a = await client.get("/api/v1/history", headers=headers_a)
        log_id = history_a.json()["items"][0]["id"]

        read_b = await client.get(f"/api/v1/history/{log_id}", headers=headers_b)
        delete_b = await client.delete(f"/api/v1/history/{log_id}", headers=headers_b)

    assert read_b.status_code == 404
    assert delete_b.status_code == 404


@pytest.mark.asyncio
async def test_history_pagination_is_newest_first():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await auth_headers(client, f"Paging {uuid.uuid4().hex[:6]}")
        for question in ("first", "second", "third"):
            response = await _ask(client, headers, question)
            assert response.status_code == 200
        page = await client.get(
            "/api/v1/history?limit=2", headers=headers
        )

    assert page.status_code == 200
    assert page.json()["total"] == 3
    assert len(page.json()["items"]) == 2
    assert [item["question"] for item in page.json()["items"]] == ["third", "second"]


@pytest.mark.asyncio
async def test_history_delete_then_get_returns_404():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await auth_headers(client, f"Delete {uuid.uuid4().hex[:6]}")
        await _ask(client, headers)
        history = await client.get("/api/v1/history", headers=headers)
        log_id = history.json()["items"][0]["id"]
        deleted = await client.delete(f"/api/v1/history/{log_id}", headers=headers)
        fetched = await client.get(f"/api/v1/history/{log_id}", headers=headers)

    assert deleted.status_code == 204
    assert fetched.status_code == 404


@pytest.mark.asyncio
async def test_history_requires_authentication():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/history")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_member_sees_only_own_history_while_owner_sees_tenant_history():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        owner_headers = await auth_headers(client, f"Members {uuid.uuid4().hex[:6]}")
        me = await client.get("/api/v1/auth/me", headers=owner_headers)
        tenant_id = uuid.UUID(me.json()["tenant_id"])

        async with AsyncSessionLocal() as db:
            member = User(
                tenant_id=tenant_id,
                email=f"member-{uuid.uuid4().hex[:8]}@example.com",
                hashed_password="unused-test-password-hash",
                role=UserRole.MEMBER,
            )
            db.add(member)
            await db.flush()
            member_id = member.id
            await db.commit()

        member_headers = {
            "Authorization": f"Bearer {create_access_token(str(member_id), str(tenant_id))}"
        }
        await _ask(client, owner_headers, "Owner question")
        await _ask(client, member_headers, "Member question")
        owner_history = await client.get("/api/v1/history", headers=owner_headers)
        member_history = await client.get("/api/v1/history", headers=member_headers)

    assert owner_history.status_code == 200
    assert owner_history.json()["total"] == 2
    assert member_history.status_code == 200
    assert member_history.json()["total"] == 1
    assert member_history.json()["items"][0]["question"] == "Member question"
