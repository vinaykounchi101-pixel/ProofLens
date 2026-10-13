"""PDF validation, page-level text extraction, and scan detection (FR-02, FR-03)."""

import io
import re
from typing import List, NamedTuple
import pypdf
from app.core.errors import UnprocessablePDFException, ValidationException


class PageExtract(NamedTuple):
    page_number: int  # 1-based
    text: str
    char_count: int


class PDFService:
    @staticmethod
    def validate_pdf_bytes(file_bytes: bytes, max_size_bytes: int = 15 * 1024 * 1024) -> None:
        """Validates PDF size, magic bytes, and basic header structure."""
        if len(file_bytes) == 0:
            raise ValidationException("Uploaded file is empty (0 bytes).")

        if len(file_bytes) > max_size_bytes:
            raise ValidationException(
                f"File size ({len(file_bytes)} bytes) exceeds the maximum allowed limit of {max_size_bytes} bytes."
            )

        if not file_bytes.startswith(b"%PDF-"):
            raise ValidationException("Uploaded file does not have a valid PDF header signature.")

    @staticmethod
    def extract_pages(file_bytes: bytes, max_pages: int = 50) -> List[PageExtract]:
        """
        Extracts text from PDF page-by-page while preserving 1-based page numbering.
        Enforces page limits and detects scanned / unusable image-only PDFs.
        """
        PDFService.validate_pdf_bytes(file_bytes)

        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        except Exception as e:
            raise UnprocessablePDFException(f"Failed to parse PDF document structure: {str(e)}")

        if reader.is_encrypted:
            raise UnprocessablePDFException(
                "PDF document is password-protected or encrypted. Encrypted PDFs are not supported."
            )

        total_pages = len(reader.pages)
        if total_pages == 0:
            raise UnprocessablePDFException("PDF contains 0 pages.")

        if total_pages > max_pages:
            raise ValidationException(
                f"PDF has {total_pages} pages, which exceeds the maximum limit of {max_pages} pages for the free-tier MVP."
            )

        extracted_pages: List[PageExtract] = []
        total_chars = 0
        blank_pages = 0

        for idx, page in enumerate(reader.pages):
            page_number = idx + 1  # 1-based
            try:
                raw_text = page.extract_text() or ""
            except Exception:
                raw_text = ""

            # Conservative normalization:
            # Normalize line breaks and multiple consecutive spaces, but preserve paragraphs
            cleaned_text = re.sub(r"\r\n|\r", "\n", raw_text)
            cleaned_text = re.sub(r"[ \t]+", " ", cleaned_text)
            cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text).strip()

            char_count = len(cleaned_text)
            total_chars += char_count

            if char_count < 10:
                blank_pages += 1

            extracted_pages.append(
                PageExtract(
                    page_number=page_number,
                    text=cleaned_text,
                    char_count=char_count,
                )
            )

        # If total characters across document is 0, then the document has no digital text layer (scanned/image-only)
        if total_chars == 0:
            raise UnprocessablePDFException(
                "Document contains no extractable text. Scanned or image-only PDFs without an embedded text layer are not supported."
            )

        return extracted_pages


pdf_service = PDFService()
