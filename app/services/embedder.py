"""
Generate embeddings using fastembed (local ONNX model).
No API key required. Runs entirely inside the worker container.
Model: sentence-transformers/all-MiniLM-L6-v2 → 384 dimensions.
"""
from fastembed import TextEmbedding
from app.models.chunk import EMBEDDING_DIMENSIONS

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Module-level singleton — model is loaded once per worker process
_model: TextEmbedding | None = None


def get_model() -> TextEmbedding:
    global _model
    if _model is None:
        _model = TextEmbedding(model_name=EMBEDDING_MODEL)
    return _model


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Add an "embedding" key (list[float], length 384) to each chunk dict.
    Uses local fastembed model — no network calls after first load.
    """
    if not chunks:
        return chunks

    model = get_model()
    texts = [c["content"] for c in chunks]

    # fastembed.embed() returns a generator of numpy arrays
    embeddings = list(model.embed(texts))

    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding.tolist()

    return chunks
