"""Audio storage provider abstraction + deterministic stubs.

Stores audio OUT of the database (we never put large blobs in Postgres). The
database keeps only metadata (see AudioRecording). Mock providers keep bytes in
memory or on local disk; real object storage (S3/Cloudflare R2) is wired later
behind this same interface. No external calls here.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Optional
from uuid import uuid4


@dataclass
class StoredAudio:
    storage_key: str
    content_type: str
    size_bytes: int
    checksum_sha256: str
    provider: str
    url: Optional[str] = None
    duration_ms: Optional[int] = None
    metadata: dict = field(default_factory=dict)


class AudioStorageError(Exception):
    """Storage save/lookup/delete failed. Mapped to a safe degraded response."""


class AudioStorageProvider(ABC):
    provider: str = "abstract"

    @abstractmethod
    async def save_audio(
        self,
        data: bytes,
        *,
        content_type: str,
        duration_ms: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> StoredAudio:
        raise NotImplementedError

    @abstractmethod
    async def get_signed_url(self, storage_key: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def delete_audio(self, storage_key: str) -> None:
        raise NotImplementedError


class InMemoryAudioStorage(AudioStorageProvider):
    """Default for tests/dev. Keeps bytes in a process dict; never persisted."""

    provider = "memory"

    def __init__(self, signed_url_ttl_seconds: int = 300) -> None:
        self._store: dict[str, bytes] = {}
        self._ttl = signed_url_ttl_seconds

    async def save_audio(
        self, data: bytes, *, content_type: str, duration_ms: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> StoredAudio:
        key = uuid4().hex
        self._store[key] = data
        return StoredAudio(
            storage_key=key, content_type=content_type, size_bytes=len(data),
            checksum_sha256=sha256(data).hexdigest(), provider=self.provider,
            url=None, duration_ms=duration_ms, metadata=metadata or {},
        )

    async def get_signed_url(self, storage_key: str) -> str:
        if storage_key not in self._store:
            raise AudioStorageError(f"unknown storage_key: {storage_key}")
        return f"memory://{storage_key}?ttl={self._ttl}"  # placeholder, not a real URL

    async def delete_audio(self, storage_key: str) -> None:
        self._store.pop(storage_key, None)


class LocalAudioStorage(AudioStorageProvider):
    """Writes audio to a local directory (dev). Signed URL is a file:// placeholder."""

    provider = "local"

    def __init__(self, base_path: str, signed_url_ttl_seconds: int = 300) -> None:
        self._base = Path(base_path)
        self._ttl = signed_url_ttl_seconds

    async def save_audio(
        self, data: bytes, *, content_type: str, duration_ms: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> StoredAudio:
        try:
            self._base.mkdir(parents=True, exist_ok=True)
            key = uuid4().hex
            (self._base / key).write_bytes(data)
        except OSError as exc:
            raise AudioStorageError(f"local storage write failed: {type(exc).__name__}") from exc
        return StoredAudio(
            storage_key=key, content_type=content_type, size_bytes=len(data),
            checksum_sha256=sha256(data).hexdigest(), provider=self.provider,
            url=None, duration_ms=duration_ms, metadata=metadata or {},
        )

    async def get_signed_url(self, storage_key: str) -> str:
        path = self._base / storage_key
        if not path.exists():
            raise AudioStorageError(f"unknown storage_key: {storage_key}")
        return f"file://{path.resolve()}"  # placeholder; not a signed URL

    async def delete_audio(self, storage_key: str) -> None:
        (self._base / storage_key).unlink(missing_ok=True)
