import uuid
from unittest.mock import patch
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import AsyncSessionLocal
from app.models.document import Document, DocumentStatus, DocumentType
from app.models.chunk import Chunk
from app.services.search import reciprocal_rank_fusion
from tests.conftest import auth_headers


def _vector(first, second=0.0):
    vector = [0.0] * 384
    vector[0] = first
    vector[1] = second
    return vector


async def _insert_chunks(tenant_id, chunk_specs):
    async with AsyncSessionLocal() as db:
        document = Document(
            tenant_id=tenant_id,
            filename=f"{uuid.uuid4().hex}.pdf",
            original_filename="hybrid.pdf",
            file_type=DocumentType.PDF,
            file_size_bytes=128,
            storage_path="/tmp/hybrid.pdf",
            status=DocumentStatus.READY,
        )
        db.add(document)
        await db.flush()
        for index, (content, embedding) in enumerate(chunk_specs):
            db.add(Chunk(
                document_id=document.id,
                tenant_id=tenant_id,
                content=content,
                chunk_index=index,
                page_number=index + 1,
                embedding=embedding,
            ))
        await db.commit()
        return document.id


async def _tenant_id(client, headers):
    response = await client.get("/api/v1/auth/me", headers=headers)
    return uuid.UUID(response.json()["tenant_id"])


def test_reciprocal_rank_fusion_combines_rankings_and_respects_limit():
    both = {"chunk_id": "both", "content": "from vector"}
    vector_only = {"chunk_id": "vector", "content": "vector"}
    keyword_only = {"chunk_id": "keyword", "content": "keyword"}
    results = reciprocal_rank_fusion(
        [[both, vector_only], [both, keyword_only]], top_k=2
    )

    assert len(results) == 2
    assert results[0]["chunk_id"] == "both"
    assert results[0]["content"] == "from vector"
    assert results[0]["score"] == round(1 / 61 + 1 / 61, 6)


@pytest.mark.asyncio
async def test_keyword_mode_finds_distinctive_word_only():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await auth_headers(client, f"Keyword {uuid.uuid4().hex[:6]}")
        tenant_id = await _tenant_id(client, headers)
        await _insert_chunks(tenant_id, [
            ("The rare term zebracorn is present here", _vector(1.0)),
            ("This passage contains ordinary words", _vector(0.0, 1.0)),
        ])
        found = await client.post(
            "/api/v1/search",
            json={"query": "zebracorn", "mode": "keyword", "top_k": 5},
            headers=headers,
        )
        absent = await client.post(
            "/api/v1/search",
            json={"query": "unfindablewordxyz", "mode": "keyword", "top_k": 5},
            headers=headers,
        )

    assert found.status_code == 200
    assert len(found.json()["results"]) == 1
    assert "zebracorn" in found.json()["results"][0]["content"]
    assert absent.status_code == 200
    assert absent.json()["results"] == []


@pytest.mark.asyncio
async def test_hybrid_finds_keyword_chunk_far_from_vector_query():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await auth_headers(client, f"Hybrid {uuid.uuid4().hex[:6]}")
        tenant_id = await _tenant_id(client, headers)
        await _insert_chunks(tenant_id, [
            ("Common unrelated passage", _vector(1.0)),
            ("Distinctive zebracorn passage", _vector(0.0, 1.0)),
        ])
        with patch("app.services.search.embed_query", return_value=_vector(1.0)):
            response = await client.post(
                "/api/v1/search",
                json={"query": "zebracorn", "mode": "hybrid", "top_k": 1},
                headers=headers,
            )

    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert "zebracorn" in response.json()["results"][0]["content"]


@pytest.mark.asyncio
async def test_vector_mode_preserves_vector_search_results():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await auth_headers(client, f"Vector {uuid.uuid4().hex[:6]}")
        tenant_id = await _tenant_id(client, headers)
        await _insert_chunks(tenant_id, [
            ("First vector passage", _vector(1.0)),
            ("Second vector passage", _vector(0.0, 1.0)),
        ])
        with patch("app.services.search.embed_query", return_value=_vector(1.0)):
            response = await client.post(
                "/api/v1/search",
                json={"query": "vector query", "mode": "vector", "top_k": 1},
                headers=headers,
            )

    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["content"] == "First vector passage"


@pytest.mark.asyncio
async def test_invalid_search_mode_is_rejected():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await auth_headers(client, f"Invalid {uuid.uuid4().hex[:6]}")
        response = await client.post(
            "/api/v1/search",
            json={"query": "test", "mode": "other"},
            headers=headers,
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_keyword_search_is_tenant_isolated():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers_a = await auth_headers(client, f"Tenant A {uuid.uuid4().hex[:6]}")
        headers_b = await auth_headers(client, f"Tenant B {uuid.uuid4().hex[:6]}")
        tenant_a = await _tenant_id(client, headers_a)
        await _insert_chunks(tenant_a, [
            ("Private zebracorn keyword", _vector(1.0)),
        ])
        response = await client.post(
            "/api/v1/search",
            json={"query": "zebracorn", "mode": "keyword"},
            headers=headers_b,
        )

    assert response.status_code == 200
    assert response.json()["results"] == []


@pytest.mark.asyncio
async def test_search_requires_authentication():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/search", json={"query": "zebracorn"}
        )

    assert response.status_code == 401
