from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.config import get_settings
import redis.asyncio as aioredis

router = APIRouter()
settings = get_settings()


@router.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.app_env,
    }


@router.get("/health/detailed", tags=["Health"])
async def detailed_health(db: AsyncSession = Depends(get_db)):
    checks = {}

    # Database check
    try:
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        # Check pgvector
        vec_result = await db.execute(
            text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'")
        )
        vec = vec_result.fetchone()
        checks["database"] = {
            "status": "healthy",
            "pgvector": vec.extversion if vec else "not installed"
        }
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}

    # Redis check
    try:
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        checks["redis"] = {"status": "healthy"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}

    overall = "healthy" if all(
        v["status"] == "healthy" for v in checks.values()
    ) else "degraded"

    return {"status": overall, "checks": checks}
