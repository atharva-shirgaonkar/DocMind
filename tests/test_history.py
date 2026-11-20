import uuid
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from app.models.user import User, UserRole
from tests.conftest import auth_headers

    "chunk_id": uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
    "chunk_index": 0,
