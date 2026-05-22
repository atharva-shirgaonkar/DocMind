from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.config import get_settings
from app.api.health import router as health_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 {settings.app_name} starting in {settings.app_env} mode")
    # Import models so metadata is populated before create_all
    from app.models import Tenant, User, Document, Chunk  # noqa
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

app.include_router(health_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "DocMind",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
