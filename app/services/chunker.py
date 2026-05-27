"""
Split extracted page text into overlapping chunks.

Strategy:
  - Split on sentence boundaries (double-newline, then single-newline,
    then ". ") to keep semantic units together.
  - Slide a window of CHUNK_SIZE tokens (approx. characters / 4)
    with CHUNK_OVERLAP overlap.
  - Each chunk carries the source page_number for citation.

Returns a list of dicts:
  {
    "content":       str,
    "chunk_index":   int,   # global position across whole document
    "page_number":   int,
    "char_count":    int,
  }
"""

CHUNK_SIZE = 800        # target characters per chunk
CHUNK_OVERLAP = 150     # overlap between consecutive chunks
MIN_CHUNK_CHARS = 50    # discard chunks shorter than this


def _split_into_sentences(text: str) -> list[str]:
    """Rough sentence splitter — good enough for chunking purposes."""
    import re
    # Split on paragraph breaks first, then sentence-ending punctuation
    parts = re.split(r"\n\n+", text)
    sentences = []
    for part in parts:
        sub = re.split(r"(?<=[.!?])\s+", part.strip())
        sentences.extend([s.strip() for s in sub if s.strip()])
    return sentences


def _split_long_text(text: str) -> list[str]:
    """Split a single oversized sentence into overlapping character windows."""
    windows = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        content = text[start:end].strip()
        if len(content) >= MIN_CHUNK_CHARS:
            windows.append(content)
        if end >= len(text):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return windows


def chunk_pages(pages: list[tuple[int, str]]) -> list[dict]:
    """
    Accept [(page_number, text), ...] from the extractor.
    Return list of chunk dicts.
    """
    chunks = []
    chunk_index = 0

    for page_number, page_text in pages:
