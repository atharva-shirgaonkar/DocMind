import pytest
from unittest.mock import patch, MagicMock
from app.services.chunker import chunk_pages
from app.services.extractor import extract_text
import tempfile
import os


# ── Chunker tests ──────────────────────────────────────────────

def test_chunk_pages_basic():
    pages = [(1, "Hello world. " * 100)]
    chunks = chunk_pages(pages)
    assert len(chunks) > 1
    for c in chunks:
        assert "content" in c
        assert "chunk_index" in c
        assert "page_number" in c
        assert c["page_number"] == 1


def test_chunk_pages_preserves_order():
    pages = [(1, "Sentence one. " * 60), (2, "Sentence two. " * 60)]
    chunks = chunk_pages(pages)
    indices = [c["chunk_index"] for c in chunks]
    assert indices == sorted(indices)


def test_chunk_pages_empty_input():
    assert chunk_pages([]) == []


def test_chunk_pages_short_text_below_min():
    # A single very short page should still produce one chunk
    pages = [(1, "Short text that is long enough to pass minimum check.")]
    chunks = chunk_pages(pages)
    assert len(chunks) == 1


def test_chunk_pages_overlap():
    long_text = "Word " * 400  # 2000 chars
    pages = [(1, long_text)]
    chunks = chunk_pages(pages)
    # With overlap, content of consecutive chunks should share some text
    assert len(chunks) >= 2


# ── Extractor tests ────────────────────────────────────────────

def test_extractor_missing_file():
    with pytest.raises(ValueError, match="File not found"):
        extract_text("/nonexistent/path/file.pdf", "pdf")


def test_extractor_unknown_type():
    with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
        f.write(b"dummy")
        tmp = f.name
    try:
        with pytest.raises(ValueError, match="Unknown file type"):
            extract_text(tmp, "xyz")
    finally:
        os.remove(tmp)


# ── Embedder tests (mocked — no real API calls) ────────────────

def test_embed_chunks_mocked():
    from app.services.embedder import embed_chunks

    fake_embedding = [0.1] * 1536
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=fake_embedding)]

    with patch("app.services.embedder.OpenAI") as MockOpenAI:
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        MockOpenAI.return_value = mock_client

        chunks = [{"content": "Test chunk one", "chunk_index": 0,
                   "page_number": 1, "char_count": 14}]
        result = embed_chunks(chunks)

    assert "embedding" in result[0]
    assert len(result[0]["embedding"]) == 1536


def test_embed_chunks_empty():
    from app.services.embedder import embed_chunks
    assert embed_chunks([]) == []
