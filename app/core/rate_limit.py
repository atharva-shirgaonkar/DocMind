import redis.asyncio as aioredis
from fastapi import HTTPException, Request, Depends
from app.config import get_settings
from app.models.user import User


async def _hit(key: str, limit: int, window: int = 60) -> None:
    """Fixed-window counter. Fail-open if Redis is unavailable."""
    settings = get_settings()
    if not settings.rate_limit_enabled:
        return
    r = None
    try:
        r = aioredis.from_url(settings.redis_url)
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, window)
        if count > limit:
            ttl = await r.ttl(key)
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Try again shortly.",
                headers={"Retry-After": str(max(ttl, 1))},
            )
    except HTTPException:
        raise
    except Exception:
        return  # fail-open
    finally:
        if r is not None:
            try:
                await r.aclose()
            except Exception:
                pass


async def auth_rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    limit = get_settings().auth_rate_limit_per_minute
    await _hit(f"rl:auth:{ip}", limit)


def user_rate_limit():
    """Returns a dependency limiting per authenticated user."""
    from app.api.deps import get_current_user

    async def _dep(user: User = Depends(get_current_user)) -> User:
        limit = get_settings().query_rate_limit_per_minute
        await _hit(f"rl:q:{user.id}", limit)
        return user

    return _dep
