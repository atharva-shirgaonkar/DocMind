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
    "chunk_index": 0,
