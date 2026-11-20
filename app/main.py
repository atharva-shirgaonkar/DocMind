from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.config import get_settings
from app.api.health import router as health_router
from app.api.documents import router as documents_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 {settings.app_name} starting in {settings.app_env} mode")
    # Import models so metadata is populated before create_all
    from app.models import Tenant, User, Document, Chunk, UsageEvent, QueryLog  # noqa
    from app.database import create_tables
    await create_tables()
    print("✅ Database tables verified")
    yield
    print(f"🛑 {settings.app_name} shutting down")


app = FastAPI(
    title="DocMind",
    description="Multi-tenant RAG engine — upload documents, ask questions, get cited answers.",
    version="0.1.0",
    lifespan=lifespan,
)

from fastapi.middleware.cors import CORSMiddleware
from app.core.middleware import RequestContextMiddleware

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
    expose_headers=["X-Request-ID", "Retry-After"],
)
app.add_middleware(RequestContextMiddleware)

app.include_router(health_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
from app.api.search import router as search_router
app.include_router(search_router, prefix="/api/v1")
from app.api.ask import router as ask_router
app.include_router(ask_router, prefix="/api/v1")
from app.api.auth import router as auth_router
app.include_router(auth_router, prefix="/api/v1")
from app.api.history import router as history_router
app.include_router(history_router, prefix="/api/v1")
from app.api.metrics import router as metrics_router
app.include_router(metrics_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "DocMind",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
