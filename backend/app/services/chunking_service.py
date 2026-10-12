"""Page-aware text chunker with paragraph and sentence priority (FR-04)."""

import re
from typing import List, NamedTuple
from app.services.pdf_service import PageExtract


class ChunkItem(NamedTuple):
    chunk_index: int
    page_number: int
    end_page_number: int
    content: str
    token_count: int


class PageAwareChunker:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_pages(self, pages: List[PageExtract]) -> List[ChunkItem]:
        """
        Takes page extracts and produces chunks with source page provenance.
        Chunks preserve paragraph boundaries where feasible.
        """
        chunks: List[ChunkItem] = []
        chunk_idx = 0

        # Build list of (page_num, text_block)
        for page in pages:
            if not page.text.strip():
                continue

            text = page.text
            start_pos = 0
            text_len = len(text)

            while start_pos < text_len:
                end_pos = min(start_pos + self.chunk_size, text_len)

                # If we're not at the end of the page text, search for split point
                if end_pos < text_len:
                    # Look for paragraph break
                    para_break = text.rfind("\n\n", start_pos, end_pos)
                    if para_break != -1 and para_break > start_pos + self.chunk_size // 3:
                        end_pos = para_break
                    else:
                        # Look for sentence boundary
                        sentence_match = list(re.finditer(r"[.!?]\s+", text[start_pos:end_pos]))
                        if sentence_match:
                            last_punct = sentence_match[-1].end()
                            if last_punct > self.chunk_size // 3:
                                end_pos = start_pos + last_punct

                chunk_text = text[start_pos:end_pos].strip()
                if chunk_text:
                    token_count = max(1, len(chunk_text) // 4)
                    chunks.append(
                        ChunkItem(
                            chunk_index=chunk_idx,
                            page_number=page.page_number,
                            end_page_number=page.page_number,
                            content=chunk_text,
                            token_count=token_count,
                        )
                    )
                    chunk_idx += 1

                # Advance with overlap
                if end_pos >= text_len:
                    break
                start_pos = max(start_pos + 1, end_pos - self.chunk_overlap)

        return chunks


chunker = PageAwareChunker()
