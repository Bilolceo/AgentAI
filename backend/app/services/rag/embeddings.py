"""Embedding provayderi.

TODO: yakuniy provayderni tanlash (Azure OpenAI / Voyage / OpenAI).
settings.embedding_provider va settings.embedding_dim bilan moslang.
"""
from __future__ import annotations

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("rag.embeddings")


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Matnlar ro'yxatini embedding vektorlariga aylantiradi."""
    # TODO: settings.embedding_provider bo'yicha haqiqiy API chaqiruvi.
    raise NotImplementedError(
        f"embed_texts TODO — provayder '{settings.embedding_provider}' ulanmagan"
    )


async def embed_query(query: str) -> list[float]:
    (vec,) = await embed_texts([query])
    return vec
