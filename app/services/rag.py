from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.search import search_chunks
from app.services.llm import generate_chat

SYSTEM_PROMPT = (
    "You are DocMind, an assistant that answers questions using ONLY "
    "the numbered context passages provided. Rules:\n"
    "1. Use only information from the passages. Never use outside "
    "knowledge.\n"
    "2. Cite every claim with its passage number in square brackets, "
    "like [1] or [2][3].\n"
    "3. If the passages do not contain the answer, reply exactly: "
    "\"I couldn't find the answer in the uploaded documents.\"\n"
    "4. Be concise. The passages may contain odd characters from PDF "
    "extraction; ignore them."
)

NO_ANSWER = "I couldn't find the answer in the uploaded documents."


def _dedupe(candidates: list[dict], limit: int) -> list[dict]:
    """Drop chunks with identical text (e.g. same file uploaded twice)."""
    seen: set[str] = set()
    unique: list[dict] = []
    for c in candidates:
        key = " ".join(c["content"].split()).lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(c)
        if len(unique) == limit:
            break
    return unique


async def answer_question(
    db: AsyncSession,
    tenant_id: UUID,
    question: str,
    top_k: int = 4,
    document_id: UUID | None = None,
) -> dict:
    # Over-fetch, then dedupe, so duplicates do not crowd out context
    candidates = await search_chunks(
        db=db,
        tenant_id=tenant_id,
        query=question,
        top_k=top_k * 3,
        document_id=document_id,
    )
    chunks = _dedupe(candidates, top_k)

    if not chunks:
        return {"question": question, "answer": NO_ANSWER, "sources": []}

    context_blocks = []
    for i, c in enumerate(chunks, start=1):
        page = f", page {c['page_number']}" if c["page_number"] else ""
        context_blocks.append(
            f"[{i}] (source: {c['document_name']}{page})\n{c['content']}"
        )
    context = "\n\n".join(context_blocks)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Context passages:\n\n{context}\n\n"
                       f"Question: {question}",
        },
    ]
    answer = await generate_chat(messages)

    sources = [
        {
            "citation_number": i,
            "document_id": c["document_id"],
            "document_name": c["document_name"],
            "page_number": c["page_number"],
            "chunk_index": c["chunk_index"],
            "snippet": c["content"][:300],
            "score": c["score"],
        }
        for i, c in enumerate(chunks, start=1)
    ]
    return {"question": question, "answer": answer, "sources": sources}
