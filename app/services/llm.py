import httpx
from fastapi import HTTPException
from app.config import get_settings


async def generate_chat(
    messages: list[dict],
    temperature: float = 0.1,
    max_tokens: int = 700,
) -> str:
    """Call an OpenAI-compatible chat completions endpoint."""
    settings = get_settings()
    if not settings.groq_api_key:
        raise HTTPException(
            status_code=503,
            detail="LLM is not configured. Set GROQ_API_KEY in .env.",
        )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.llm_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.llm_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502, detail=f"LLM request failed: {e}"
        )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"LLM provider error {resp.status_code}: "
                   f"{resp.text[:300]}",
        )

    return resp.json()["choices"][0]["message"]["content"].strip()
