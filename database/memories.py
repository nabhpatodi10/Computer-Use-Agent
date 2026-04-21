import asyncio
import hashlib
import json
import sqlite3
from datetime import datetime, timezone

import sqlite_vec
from langchain_community.vectorstores import SQLiteVec
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from sqlite_vec import serialize_float32

from settings import settings

TABLE = "user_memories"


class UserMemoryRepository:
    """CRUD + vector search over user memories. Wraps SQLiteVec (which owns
    embedding + MATCH KNN) and augments it with dedup, list, edit, delete
    via raw SQL on the same connection.

    Not session-scoped — memories are about the user, not a conversation.
    """

    def __init__(self) -> None:
        self._embeddings = OllamaEmbeddings(
            model=settings.embedding_model,
            base_url=settings.ollama_base_url,
        )
        # `check_same_thread=False` because repo methods wrap sync SQL
        # in `asyncio.to_thread`, which dispatches to worker threads.
        # For this app's workload (single user, sequential ops), SQLite's
        # serialized threading mode handles it without an app-level lock.
        conn = sqlite3.connect(
            str(settings.sqlite_db_file), check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        self._conn = conn
        self._store = SQLiteVec(
            table=TABLE,
            connection=conn,
            embedding=self._embeddings,
        )

    @staticmethod
    def _hash(content: str) -> str:
        return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _row_to_dict(self, row) -> dict:
        meta = json.loads(row["metadata"]) if row["metadata"] else {}
        return {"id": row["rowid"], "text": row["text"], "metadata": meta}

    def _existing_by_hash(self, content_hash: str) -> dict | None:
        row = self._conn.execute(
            f"SELECT rowid, text, metadata FROM {TABLE} "
            "WHERE json_extract(metadata, '$.content_hash') = ?",
            (content_hash,),
        ).fetchone()
        return self._row_to_dict(row) if row else None

    async def add(self, content: str, category: str | None = None) -> dict:
        h = self._hash(content)
        existing = await asyncio.to_thread(self._existing_by_hash, h)
        if existing:
            return existing

        now = self._now()
        metadata = {
            "content_hash": h,
            "category": category,
            "created_at": now,
            "updated_at": now,
        }
        ids = await self._store.aadd_texts(texts=[content], metadatas=[metadata])
        return {"id": int(ids[0]), "text": content, "metadata": metadata}

    async def edit(
        self,
        memory_id: int,
        content: str,
        category: str | None = None,
    ) -> dict:
        h = self._hash(content)
        collision = await asyncio.to_thread(self._existing_by_hash, h)
        if collision and collision["id"] != memory_id:
            raise ValueError(
                f"Another memory (#{collision['id']}) already has this content"
            )

        embedding = await self._embeddings.aembed_query(content)
        blob = serialize_float32(embedding)

        def _update():
            row = self._conn.execute(
                f"SELECT metadata FROM {TABLE} WHERE rowid = ?", (memory_id,)
            ).fetchone()
            if row is None:
                raise LookupError(f"Memory {memory_id} not found")
            meta = json.loads(row["metadata"]) if row["metadata"] else {}
            meta["content_hash"] = h
            if category is not None:
                meta["category"] = category
            meta["updated_at"] = self._now()
            self._conn.execute(
                f"UPDATE {TABLE} SET text = ?, metadata = ?, text_embedding = ? "
                "WHERE rowid = ?",
                (content, json.dumps(meta), blob, memory_id),
            )
            self._conn.commit()
            return meta

        meta = await asyncio.to_thread(_update)
        return {"id": memory_id, "text": content, "metadata": meta}

    async def delete(self, memory_id: int) -> bool:
        def _del():
            cur = self._conn.execute(
                f"DELETE FROM {TABLE} WHERE rowid = ?", (memory_id,)
            )
            self._conn.commit()
            return cur.rowcount > 0

        return await asyncio.to_thread(_del)

    async def list_all(
        self,
        category: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        def _list():
            if category is None:
                sql = (
                    f"SELECT rowid, text, metadata FROM {TABLE} "
                    "ORDER BY json_extract(metadata, '$.updated_at') DESC LIMIT ?"
                )
                params = (limit,)
            else:
                sql = (
                    f"SELECT rowid, text, metadata FROM {TABLE} "
                    "WHERE json_extract(metadata, '$.category') = ? "
                    "ORDER BY json_extract(metadata, '$.updated_at') DESC LIMIT ?"
                )
                params = (category, limit)
            rows = self._conn.execute(sql, params).fetchall()
            return [self._row_to_dict(r) for r in rows]

        return await asyncio.to_thread(_list)

    async def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[tuple[Document, float]]:
        return await self._store.asimilarity_search_with_score(query=query, k=limit)

    def close(self) -> None:
        self._conn.close()
