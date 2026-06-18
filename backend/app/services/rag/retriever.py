"""pgvector orqali bilim bazasidan o'xshashlik qidiruvi."""
from __future__ import annotations

from sqlalchemy import select

from app.core.db import SessionLocal
from app.core.logging import get_logger
from app.models.knowledge import KnowledgeChunk
from app.services.rag.embeddings import embed_query

log = get_logger("rag.retriever")


async def search_knowledge(query: str, *, top_k: int = 4) -> list[str]:
    """So'rovga eng yaqin `top_k` chunk matnini qaytaradi (cosine masofa)."""
    query_vec = await embed_query(query)
    async with SessionLocal() as session:
        stmt = (
            select(KnowledgeChunk.content)
            .order_by(KnowledgeChunk.embedding.cosine_distance(query_vec))
            .limit(top_k)
        )
        rows = await session.execute(stmt)
        return [r[0] for r in rows.all()]
