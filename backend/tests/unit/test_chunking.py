"""Unit tests for text chunker and provenance tracking (FR-04)."""

from app.services.pdf_service import PageExtract
from app.services.chunking_service import PageAwareChunker


def test_chunking_preserves_page_provenance():
    chunker = PageAwareChunker(chunk_size=100, chunk_overlap=20)
    pages = [
        PageExtract(page_number=1, text="First sentence on page one. Second sentence on page one.", char_count=56),
        PageExtract(page_number=2, text="Third sentence on page two. Fourth sentence on page two.", char_count=56),
    ]

    chunks = chunker.chunk_pages(pages)
    assert len(chunks) >= 2
    assert chunks[0].page_number == 1
    assert chunks[-1].page_number == 2
    for c in chunks:
        assert c.token_count > 0
        assert len(c.content) > 0


def test_chunking_paragraph_boundary_split():
    chunker = PageAwareChunker(chunk_size=120, chunk_overlap=20)
    pages = [
        PageExtract(
            page_number=1,
            text="First paragraph with lots of words.\n\nSecond paragraph that should split cleanly here.",
            char_count=88,
        )
    ]
    chunks = chunker.chunk_pages(pages)
    assert any("First paragraph" in c.content for c in chunks)
    assert any("Second paragraph" in c.content for c in chunks)
