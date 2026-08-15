"""Certificate storage — local filesystem now, signed URLs later.

The interface is deliberately tiny (save/open) so the Phase 9 deployment can
swap in a GCS implementation (signed URLs, private bucket) without touching
the API layer. Local files live under Settings.certificate_dir with opaque
generated names — the stored key is a bare filename, never a user path, so
path traversal is impossible by construction.
"""

import logging
import uuid
from pathlib import Path
from typing import Protocol

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.constants import CERTIFICATE_TYPES, MAX_CERTIFICATE_MB

logger = logging.getLogger("nearhelp.storage")


class CertificateStorage(Protocol):
    def save(self, data: bytes, filename: str) -> str: ...
    def open(self, key: str) -> tuple[bytes, str]: ...


class LocalCertificateStorage:
    """Dev/demo implementation — files on disk, owner-only download endpoint."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        self._base = Path(base_dir if base_dir is not None else get_settings().certificate_dir)
        self._base.mkdir(parents=True, exist_ok=True)

    def save(self, data: bytes, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        if ext not in CERTIFICATE_TYPES:
            allowed = ", ".join(sorted(CERTIFICATE_TYPES))
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"unsupported certificate type '{ext}' (allowed: {allowed})",
            )
        if len(data) > MAX_CERTIFICATE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"certificate exceeds {MAX_CERTIFICATE_MB} MB",
            )
        key = f"{uuid.uuid4().hex}{ext}"
        (self._base / key).write_bytes(data)
        return key

    def open(self, key: str) -> tuple[bytes, str]:
        # Bare-filename keys only; reject anything that tries to escape the base dir.
        path = (self._base / key).resolve()
        if not str(path).startswith(str(self._base.resolve())) or not path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="certificate not found"
            )
        return path.read_bytes(), CERTIFICATE_TYPES[path.suffix.lower()]


_storage: CertificateStorage | None = None


def get_certificate_storage() -> CertificateStorage:
    global _storage
    if _storage is None:
        _storage = LocalCertificateStorage()
    return _storage
