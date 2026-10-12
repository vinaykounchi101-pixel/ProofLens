"""Unit tests for PDF validation and text extraction (FR-02, FR-03)."""

import pytest
from app.core.errors import ValidationException, UnprocessablePDFException
from app.services.pdf_service import pdf_service


def test_empty_file_rejected():
    with pytest.raises(ValidationException, match="empty"):
        pdf_service.validate_pdf_bytes(b"")


def test_oversized_file_rejected():
    huge_bytes = b"%PDF-" + (b"0" * 16 * 1024 * 1024)
    with pytest.raises(ValidationException, match="exceeds the maximum allowed limit"):
        pdf_service.validate_pdf_bytes(huge_bytes)


def test_invalid_header_rejected():
    with pytest.raises(ValidationException, match="valid PDF header"):
        pdf_service.validate_pdf_bytes(b"NOT_A_PDF_FILE_HEADER")


def test_valid_pdf_extraction_page_count(sample_pdf_bytes):
    pages = pdf_service.extract_pages(sample_pdf_bytes)
    assert len(pages) == 2
    assert pages[0].page_number == 1
    assert pages[1].page_number == 2
    assert "81797" in pages[0].text
    assert "notice" in pages[1].text
