import re
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.schemas.auth import (
    RegisterRequest, TokenResponse, UserResponse, ApiKeyResponse,
)
from app.core.security import (
    hash_password, verify_password, create_access_token,
    generate_api_key, hash_api_key,
)
from app.api.deps import get_current_user
from app.core.rate_limit import auth_rate_limit

router = APIRouter(prefix="/auth", tags=["Auth"])


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:80] or "tenant"


@router.post(
    "/register", response_model=TokenResponse, status_code=201,
    dependencies=[Depends(auth_rate_limit)],
)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    email = body.email.strip().lower()
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered.")

    slug = f"{_slugify(body.tenant_name)}-{uuid.uuid4().hex[:6]}"
    tenant = Tenant(name=body.tenant_name, slug=slug)
    db.add(tenant)
    await db.flush()

    user = User(
        tenant_id=tenant.id,
        email=email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=UserRole.OWNER,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(str(user.id), str(tenant.id))
    )


@router.post(
    "/login", response_model=TokenResponse,
    dependencies=[Depends(auth_rate_limit)],
)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    email = form.username.strip().lower()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if (not user or not user.is_active
            or not verify_password(form.password, user.hashed_password)):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    return TokenResponse(
        access_token=create_access_token(str(user.id), str(user.tenant_id))
    )


@router.get("/me", response_model=UserResponse)
async def me(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tenant = (await db.execute(
        select(Tenant).where(Tenant.id == user.tenant_id)
    )).scalar_one()
    return UserResponse(
        id=user.id, email=user.email, full_name=user.full_name,
        role=user.role.value, tenant_id=tenant.id, tenant_name=tenant.name,
    )


@router.post("/api-key", response_model=ApiKeyResponse, status_code=201)
async def create_api_key(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    key = generate_api_key()
    user.api_key_hash = hash_api_key(key)
    db.add(user)
    await db.commit()
    return ApiKeyResponse(api_key=key)


@router.delete("/api-key", status_code=204)
async def revoke_api_key(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user.api_key_hash = None
    db.add(user)
    await db.commit()
