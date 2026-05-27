"""
Extract plain text (and page numbers) from PDF and DOCX files.
Returns a list of (page_number, text) tuples.
Page numbers are 1-indexed. DOCX uses page 1 throughout
(DOCX has no reliable page concept without rendering).
"""
from pathlib import Path
from pypdf import PdfReader
from docx import Document as DocxDocument
from fastapi import HTTPException


def extract_pdf(path: str) -> list[tuple[int, str]]:
    """Return [(page_num, page_text), ...] for every page."""
    pages = []
    try:
        reader = PdfReader(path)
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                pages.append((i, text))
    except Exception as e:
        raise ValueError(f"PDF extraction failed: {e}")
    return pages


def extract_docx(path: str) -> list[tuple[int, str]]:
    """Return [(1, full_text)] — DOCX treated as single logical page."""
    try:
        doc = DocxDocument(path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        full_text = "\n".join(paragraphs)
    except Exception as e:
        raise ValueError(f"DOCX extraction failed: {e}")
    return [(1, full_text)] if full_text else []


def extract_text(storage_path: str, file_type: str) -> list[tuple[int, str]]:
    """
    Dispatch to the correct extractor.
    Returns [(page_number, text), ...].
    Raises ValueError on failure.
    """
    path = Path(storage_path)
    if not path.exists():
        raise ValueError(f"File not found: {storage_path}")

    if file_type == "pdf":
        return extract_pdf(storage_path)
    elif file_type == "docx":
        return extract_docx(storage_path)
    else:
        raise ValueError(f"Unknown file type: {file_type}")
