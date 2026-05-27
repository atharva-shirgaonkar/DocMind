import pytest
import pytest_asyncio
import io
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import engine


@pytest_asyncio.fixture(autouse=True)
async def reset_engine_pool():
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_upload_pdf_success():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        fake_pdf = io.BytesIO(b"%PDF-1.4 fake pdf content")
        response = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", fake_pdf, "application/pdf")},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["original_filename"] == "test.pdf"
    assert "id" in data


@pytest.mark.asyncio
async def test_upload_docx_success():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        fake_docx = io.BytesIO(b"PK fake docx content")
        response = await client.post(
            "/api/v1/documents/upload",
            files={
                "file": (
                    "report.docx",
                    fake_docx,
                    "application/vnd.openxmlformats-officedocument"
                    ".wordprocessingml.document",
                )
            },
        )
    assert response.status_code == 201
    data = response.json()
    assert data["file_type"] == "docx"


@pytest.mark.asyncio
async def test_upload_invalid_type_rejected():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("data.csv", io.BytesIO(b"a,b,c"), "text/csv")},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_documents():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/documents/")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data
