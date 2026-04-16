"""Storage backends for pipeline artifacts.

Swap backends via STORAGE_BACKEND env var:
    supabase  (default when configured) — Supabase Storage
    s3                                  — AWS S3

If STORAGE_BACKEND is not set, get_storage_backend() returns None → local-only mode.

Bucket structure:
    base_images/{stem}.png
    illusion_images/{stem}__{KST}.png
    approved/{stem}__{KST}.png

Switching Supabase → S3: change STORAGE_BACKEND=supabase to STORAGE_BACKEND=s3
and fill in S3 credentials. No code changes required.
"""
from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Protocol


def _compress_for_upload(
    local_path: Path,
    max_dim: int = 512,
    quality: int = 92,
) -> tuple[bytes, str]:
    """Return (jpeg_bytes, remote_key_with_jpg_ext) — compresses image in-memory.

    Local file is never modified. RGBA/P images are converted to RGB before JPEG encoding.
    Resizes only if the longer side exceeds max_dim.
    """
    from PIL import Image

    img = Image.open(local_path)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > max_dim:
        ratio = max_dim / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue(), "image/jpeg"


class StorageBackend(Protocol):
    def upload(self, local_path: Path, remote_key: str) -> str:
        """Upload local file to remote storage. Returns public URL."""
        ...


class SupabaseStorageBackend:
    """Supabase Storage backend. Uploads as compressed JPEG regardless of source format."""

    BUCKET = "vqa-illusion"

    def __init__(self, url: str, key: str) -> None:
        from supabase import create_client
        self._client = create_client(url, key)
        self._max_dim: int = int(os.getenv("UPLOAD_MAX_DIM", "512"))
        self._quality: int = int(os.getenv("UPLOAD_JPEG_QUALITY", "92"))

    def upload(self, local_path: Path, remote_key: str) -> str:
        data, content_type = _compress_for_upload(local_path, self._max_dim, self._quality)
        remote_key = remote_key.rsplit(".", 1)[0] + ".jpg"
        self._client.storage.from_(self.BUCKET).upload(
            path=remote_key,
            file=data,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        return self._client.storage.from_(self.BUCKET).get_public_url(remote_key)


class S3StorageBackend:
    """AWS S3 backend. Uploads as compressed JPEG regardless of source format."""

    def __init__(self, bucket: str, region: str, access_key: str, secret_key: str) -> None:
        import boto3
        self._bucket = bucket
        self._region = region
        self._s3 = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        self._max_dim: int = int(os.getenv("UPLOAD_MAX_DIM", "512"))
        self._quality: int = int(os.getenv("UPLOAD_JPEG_QUALITY", "92"))

    def upload(self, local_path: Path, remote_key: str) -> str:
        data, content_type = _compress_for_upload(local_path, self._max_dim, self._quality)
        remote_key = remote_key.rsplit(".", 1)[0] + ".jpg"
        self._s3.put_object(
            Bucket=self._bucket,
            Key=remote_key,
            Body=data,
            ContentType=content_type,
        )
        return f"https://{self._bucket}.s3.{self._region}.amazonaws.com/{remote_key}"


_BACKENDS: dict[str, type] = {
    "supabase": SupabaseStorageBackend,
    "s3": S3StorageBackend,
}

_ENV_KEYS: dict[str, list[str]] = {
    "supabase": ["SUPABASE_URL", "SUPABASE_KEY"],
    "s3": ["S3_BUCKET_NAME", "AWS_REGION", "S3_ACCESS_KEY", "S3_SECRET_KEY"],
}


def get_storage_backend(name: str | None = None) -> StorageBackend | None:
    """Return an instantiated storage backend, or None for local-only mode.

    Returns None if STORAGE_BACKEND env var is not set (development default).
    """
    backend_name = name or os.environ.get("STORAGE_BACKEND")
    if not backend_name:
        return None  # local-only mode

    if backend_name not in _BACKENDS:
        raise ValueError(
            f"Unknown storage backend '{backend_name}'. Available: {sorted(_BACKENDS)}"
        )

    env_keys = _ENV_KEYS[backend_name]
    missing = [k for k in env_keys if not os.environ.get(k)]
    if missing:
        raise EnvironmentError(
            f"Storage backend '{backend_name}' requires env vars: {missing}"
        )

    if backend_name == "supabase":
        return SupabaseStorageBackend(
            url=os.environ["SUPABASE_URL"],
            key=os.environ["SUPABASE_KEY"],
        )
    else:  # s3
        return S3StorageBackend(
            bucket=os.environ["S3_BUCKET_NAME"],
            region=os.environ["AWS_REGION"],
            access_key=os.environ["S3_ACCESS_KEY"],
            secret_key=os.environ["S3_SECRET_KEY"],
        )
