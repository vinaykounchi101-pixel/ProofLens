"""PDF ingestion, page-aware chunking, embedding, and lifecycle service (FR-02, FR-03, FR-04, FR-11)."""

import hashlib
import uuid
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters import get_embedding_adapter
from app.core.config import settings
from app.core.logging import logger
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.services.chunking_service import chunker
from app.services.pdf_service import pdf_service
from app.services.storage_service import storage_service


class IngestionService:
    @staticmethod
    async def ingest_document(
        session: AsyncSession,
        workspace_id: str,
        original_filename: str,
        file_bytes: bytes,
        force_reindex: bool = False,
    ) -> Document:
        # Calculate SHA-256 hash
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        # Check for existing document with same hash in workspace
        dup_stmt = select(Document).where(
            Document.workspace_id == workspace_id,
            Document.file_hash_sha256 == file_hash,
            Document.status != "deleted",
        )
        dup_res = await session.execute(dup_stmt)
        existing_doc = dup_res.scalar_one_or_none()

        if existing_doc and not force_reindex and existing_doc.status == "indexed":
            logger.info("Duplicate document found and already indexed; returning existing document.")
            return existing_doc

        doc_id = existing_doc.id if existing_doc else str(uuid.uuid4())
        stored_filename = f"{doc_id}.pdf"

        # Save to local storage
        storage_service.save_file(workspace_id, stored_filename, file_bytes)

        if existing_doc:
            doc = existing_doc
            doc.status = "processing"
            doc.error_message = None
            doc.original_filename = original_filename
        else:
            doc = Document(
                id=doc_id,
                workspace_id=workspace_id,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_hash_sha256=file_hash,
                file_size_bytes=len(file_bytes),
                status="processing",
            )
            session.add(doc)

        await session.commit()
        await session.refresh(doc)

        try:
            # Stage 4: Extract text page-by-page (preserves 1-based page numbers and checks scan heuristics)
            page_extracts = pdf_service.extract_pages(file_bytes, max_pages=settings.MAX_PAGES_PER_DOCUMENT)
            total_pages = len(page_extracts)

            # Stage 8: Chunk extracted text
            chunk_items = chunker.chunk_pages(page_extracts)
            if not chunk_items:
                doc.status = "failed"
                doc.error_message = "No extractable text chunks could be formed from the document."
                await session.commit()
                return doc

            # Stage 9: Generate embeddings
            embedding_adapter = get_embedding_adapter()
            chunk_texts = [c.content for c in chunk_items]
            embeddings = await embedding_adapter.embed_documents(chunk_texts)

            # Stage 10: Atomic persistence — clear previous chunks if re-indexing
            await session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))

            for item, emb in zip(chunk_items, embeddings):
                chunk_record = DocumentChunk(
                    document_id=doc.id,
                    workspace_id=workspace_id,
                    chunk_index=item.chunk_index,
                    page_number=item.page_number,
                    end_page_number=item.end_page_number,
                    content=item.content,
                    token_count=item.token_count,
                    embedding_model=settings.EMBEDDING_MODEL,
                    embedding=emb,
                )
                session.add(chunk_record)

            # Stage 11: Mark indexed
            doc.status = "indexed"
            doc.total_pages = total_pages
            doc.total_chunks = len(chunk_items)
            doc.error_message = None
            await session.commit()
            await session.refresh(doc)
            return doc

        except Exception as exc:
            doc.status = "failed"
            doc.error_message = str(exc)
            await session.commit()
            raise

    @staticmethod
    async def retry_document(session: AsyncSession, workspace_id: str, document_id: str) -> Document:
        """Retries failed ingestion from saved disk file."""
        stmt = select(Document).where(Document.id == document_id, Document.workspace_id == workspace_id)
        res = await session.execute(stmt)
        doc = res.scalar_one_or_none()
        if not doc:
            from app.core.errors import ResourceNotFoundException
            raise ResourceNotFoundException("Document not found.")

        file_path = storage_service.get_file_path(workspace_id, doc.stored_filename)
        if not file_path.exists():
            from app.core.errors import ValidationException
            raise ValidationException("Source file missing from disk storage; retry impossible.")

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        return await IngestionService.ingest_document(
            session=session,
            workspace_id=workspace_id,
            original_filename=doc.original_filename,
            file_bytes=file_bytes,
            force_reindex=True,
        )

    @staticmethod
    async def delete_document(session: AsyncSession, workspace_id: str, document_id: str) -> None:
        """Cascades deletion of document, chunks, vectors, citations, and disk file (FR-11)."""
        stmt = select(Document).where(Document.id == document_id, Document.workspace_id == workspace_id)
        res = await session.execute(stmt)
        doc = res.scalar_one_or_none()
        if not doc:
            from app.core.errors import ResourceNotFoundException
            raise ResourceNotFoundException("Document not found.")

        storage_service.delete_file(workspace_id, doc.stored_filename)
        await session.delete(doc)
        await session.commit()


ingestion_service = IngestionService()
