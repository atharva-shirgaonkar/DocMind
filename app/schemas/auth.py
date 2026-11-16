from pydantic import BaseModel, Field
from uuid import UUID


class RegisterRequest(BaseModel):
    tenant_name: str = Field(..., min_length=2, max_length=255)
    email: str = Field(..., min_length=5, max_length=320,
                       pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(..., min_length=8, max_length=72)
    full_name: str | None = Field(None, max_length=255)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    role: str
    tenant_id: UUID
    tenant_name: str
