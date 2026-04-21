from collections.abc import AsyncGenerator

import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from settings import settings

DATABASE_URL = settings.database_url
SYNC_DATABASE_URL = settings.sync_database_url

# Note: sqlite-vec is NOT loaded on this async engine. The memory repo in
# `database/memories.py` opens its own sync sqlite3 connection (required by
# SQLiteVec anyway) and loads the extension there. Alembic uses its own
# sync engine (see alembic/env.py) with its own extension hook. If you ever
# query `user_memories_vec` through this async engine, you'll need to load
# the extension per-connection by unwrapping `AsyncAdapt_aiosqlite_connection.driver_connection`.

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


_checkpointer_conn: aiosqlite.Connection | None = None
_checkpointer: AsyncSqliteSaver | None = None


async def get_checkpointer() -> AsyncSqliteSaver:
    """LangGraph checkpointer backed by the same SQLite file as the app DB.
    Tables (`checkpoints`, `writes`) are managed by Alembic, not by setup()."""
    global _checkpointer_conn, _checkpointer
    if _checkpointer is not None:
        return _checkpointer
    _checkpointer_conn = await aiosqlite.connect(str(settings.sqlite_db_file))
    _checkpointer = AsyncSqliteSaver(conn=_checkpointer_conn)
    return _checkpointer


_memory_repo = None  # populated lazily to avoid circular import at module load


def get_memory_repo():
    """Module-level singleton `UserMemoryRepository`. Opens its own sync
    sqlite3 connection (required by SQLiteVec) and reuses it for all calls."""
    global _memory_repo
    if _memory_repo is None:
        from database.memories import UserMemoryRepository

        _memory_repo = UserMemoryRepository()
    return _memory_repo


async def close_connections() -> None:
    """Close the aiosqlite checkpointer connection, the memory repo's sync
    connection, and dispose the SQLAlchemy engine."""
    global _checkpointer_conn, _checkpointer, _memory_repo
    if _checkpointer_conn is not None:
        await _checkpointer_conn.close()
    _checkpointer_conn = None
    _checkpointer = None
    if _memory_repo is not None:
        _memory_repo.close()
    _memory_repo = None
    await engine.dispose()
