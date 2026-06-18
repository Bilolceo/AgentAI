"""Knowledge ingest — document → chunks → DB.

MVP stores text chunks without embeddings (keyword search). When an embedding
provider is configured, fill `embedding` here for the pgvector path.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.knowledge import KnowledgeChunk

log = get_logger("rag.ingest")


def chunk_text(text: str, *, size: int = 800, overlap: int = 100) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + size])
        start += size - overlap
    return [c for c in chunks if c.strip()]


async def ingest_document(
    session: AsyncSession, *, source: str, content: str, language: str | None = None
) -> int:
    """Chunk and store a document. Returns the number of chunks stored."""
    chunks = chunk_text(content)
    if not chunks:
        return 0
    session.add_all(
        KnowledgeChunk(source=source, language=language, content=c, embedding=None)
        for c in chunks
    )
    await session.commit()
    log.info("ingested", source=source, chunks=len(chunks))
    return len(chunks)
