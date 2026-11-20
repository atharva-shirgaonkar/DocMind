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


