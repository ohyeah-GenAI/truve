"""Database backend abstraction for the VQA-illusion offline pipeline.

Switch backends via DB_BACKEND env var (or auto-detect):
    supabase  — Supabase PostgreSQL (default when SUPABASE_URL is set)
    rds       — AWS MySQL RDS via SQLAlchemy (production)

If neither env var is configured, get_db() returns None → local-only mode.

Switching Supabase → RDS: set DB_BACKEND=rds and DATABASE_URL.
No code changes required.

.env (dev):
    DB_BACKEND=supabase       # or omit — auto-detected
    SUPABASE_URL=https://xxx.supabase.co
    SUPABASE_KEY=eyJ...

.env.prod:
    DB_BACKEND=rds
    DATABASE_URL=mysql+pymysql://user:pass@rds-host:3306/vqa
"""
from __future__ import annotations

import os
from typing import Any, Protocol


class DbBackend(Protocol):
    def insert(self, table: str, data: dict) -> dict:
        """Insert a row and return the inserted record."""
        ...

    def select(self, table: str, filters: dict | None = None) -> list[dict]:
        """Select rows, optionally filtered by exact-match key/value pairs."""
        ...

    def exists(self, table: str, filters: dict) -> bool:
        """Return True if at least one matching row exists."""
        ...

    def delete(self, table: str, filters: dict) -> None:
        """Delete rows matching all filters (exact-match)."""
        ...


class SupabaseDbBackend:
    """Supabase PostgreSQL backend via supabase-py client."""

    def __init__(self, url: str, key: str) -> None:
        from supabase import create_client
        self._client = create_client(url, key)

    def insert(self, table: str, data: dict) -> dict:
        result = self._client.table(table).insert(data).execute()
        return result.data[0]

    def select(self, table: str, filters: dict | None = None) -> list[dict]:
        q = self._client.table(table).select("*")
        if filters:
            for key, value in filters.items():
                q = q.eq(key, value)
        return q.execute().data

    def exists(self, table: str, filters: dict) -> bool:
        q = self._client.table(table).select("*", count="exact")
        for key, value in filters.items():
            q = q.eq(key, value)
        result = q.limit(1).execute()
        return (result.count or 0) > 0

    def delete(self, table: str, filters: dict) -> None:
        q = self._client.table(table).delete()
        for key, value in filters.items():
            q = q.eq(key, value)
        q.execute()


class RdsDbBackend:
    """AWS MySQL RDS backend via SQLAlchemy."""

    def __init__(self, database_url: str) -> None:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker

        self._engine = create_engine(database_url)
        self._Session = sessionmaker(bind=self._engine)

    def insert(self, table: str, data: dict) -> dict:
        from sqlalchemy import text

        cols = ", ".join(data.keys())
        placeholders = ", ".join(f":{k}" for k in data.keys())
        sql = text(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})")
        with self._Session() as session:
            session.execute(sql, data)
            session.commit()
        return data

    def select(self, table: str, filters: dict | None = None) -> list[dict]:
        from sqlalchemy import text

        where = ""
        if filters:
            clauses = " AND ".join(f"{k} = :{k}" for k in filters)
            where = f" WHERE {clauses}"
        sql = text(f"SELECT * FROM {table}{where}")
        with self._Session() as session:
            result = session.execute(sql, filters or {})
            keys = result.keys()
            return [dict(zip(keys, row)) for row in result.fetchall()]

    def exists(self, table: str, filters: dict) -> bool:
        rows = self.select(table, filters)
        return len(rows) > 0

    def delete(self, table: str, filters: dict) -> None:
        from sqlalchemy import text

        if not filters:
            raise ValueError("delete() requires at least one filter to prevent full-table deletion")
        clauses = " AND ".join(f"{k} = :{k}" for k in filters)
        sql = text(f"DELETE FROM {table} WHERE {clauses}")
        with self._Session() as session:
            session.execute(sql, filters)
            session.commit()


_ENV_KEYS: dict[str, list[str]] = {
    "supabase": ["SUPABASE_URL", "SUPABASE_KEY"],
    "rds": ["DATABASE_URL"],
}


def _detect_backend() -> str | None:
    if os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_KEY"):
        return "supabase"
    if os.environ.get("DATABASE_URL"):
        return "rds"
    return None


def get_db(name: str | None = None) -> DbBackend | None:
    """Return an instantiated DB backend, or None for local-only mode.

    Returns None if no DB environment variables are configured.
    """
    backend_name = name or os.environ.get("DB_BACKEND") or _detect_backend()
    if not backend_name:
        return None

    if backend_name not in _ENV_KEYS:
        raise ValueError(
            f"Unknown DB backend '{backend_name}'. Available: {sorted(_ENV_KEYS)}"
        )

    missing = [k for k in _ENV_KEYS[backend_name] if not os.environ.get(k)]
    if missing:
        raise EnvironmentError(
            f"DB backend '{backend_name}' requires env vars: {missing}"
        )

    if backend_name == "supabase":
        return SupabaseDbBackend(
            url=os.environ["SUPABASE_URL"],
            key=os.environ["SUPABASE_KEY"],
        )
    else:  # rds
        return RdsDbBackend(database_url=os.environ["DATABASE_URL"])
