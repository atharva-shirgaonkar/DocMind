from docx import Document as DocxDocument
from pypdf import PdfWriter
import pytest

from app.services.extractor import extract_text


def test_extract_docx_paragraphs(tmp_path):
    path = tmp_path / "two-paragraphs.docx"
    document = DocxDocument()
    document.add_paragraph("First paragraph.")
    document.add_paragraph("Second paragraph.")
    document.save(path)

    result = extract_text(str(path), "docx")
    assert result[0][0] == 1
    assert "First paragraph." in result[0][1]
    assert "Second paragraph." in result[0][1]


def test_extract_empty_docx_returns_empty_list(tmp_path):
    path = tmp_path / "empty.docx"
    DocxDocument().save(path)
    assert extract_text(str(path), "docx") == []


def test_corrupt_docx_raises_value_error(tmp_path):
    path = tmp_path / "corrupt.docx"
    path.write_bytes(b"not a docx archive")
    with pytest.raises(ValueError):
        extract_text(str(path), "docx")


def test_corrupt_pdf_raises_value_error(tmp_path):
    path = tmp_path / "corrupt.pdf"
    path.write_bytes(b"not a PDF")
    with pytest.raises(ValueError):
        extract_text(str(path), "pdf")


def test_blank_pdf_returns_empty_list(tmp_path):
    path = tmp_path / "blank.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with path.open("wb") as pdf_file:
        writer.write(pdf_file)
    assert extract_text(str(path), "pdf") == []
