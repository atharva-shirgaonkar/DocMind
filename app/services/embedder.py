"""
Generate embeddings via OpenAI text-embedding-3-small.

Batches chunks to stay within API rate limits.
Returns the same list of chunk dicts, each with an "embedding" key
containing a list[float] of length 1536.
"""
import time
from openai import OpenAI
from app.config import get_settings
from app.models.chunk import EMBEDDING_DIMENSIONS

settings = get_settings()

EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 100        # OpenAI allows up to 2048 inputs per request
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2.0       # seconds between retries


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Add an "embedding" key to each chunk dict.
    Processes in batches. Retries on transient errors.
    Returns the enriched chunk list.
    """
    if not chunks:
        return chunks

    client = OpenAI(api_key=settings.openai_api_key)
    texts = [c["content"] for c in chunks]

    embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i: i + BATCH_SIZE]
        for attempt in range(RETRY_ATTEMPTS):
            try:
                response = client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=batch,
                    dimensions=EMBEDDING_DIMENSIONS,
                )
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise RuntimeError(
                        f"Embedding failed after {RETRY_ATTEMPTS} attempts: {e}"
                    )
                time.sleep(RETRY_DELAY * (attempt + 1))

    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding

    return chunks
