"""RAGService — knowledge-base retrieval.

MVP uses a simple keyword (ILIKE) search so the pilot works without an embedding
provider. The pgvector path (services/rag/retriever.py) is wired in once an
embedding provider is configured.
"""
from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeChunk


class RAGService:
    """Keyword retriever over knowledge_chunks (MVP)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def retrieve(self, query: str, language: str, *, top_k: int = 4) -> list[str]:
        terms = [t for t in query.lower().split() if len(t) > 2][:6]
        if not terms:
            return []
        conditions = [KnowledgeChunk.content.ilike(f"%{t}%") for t in terms]
        stmt = (
            select(KnowledgeChunk.content)
            .where(or_(*conditions))
            .limit(top_k)
        )
        rows = await self._session.execute(stmt)
        return [r[0] for r in rows.all()]
