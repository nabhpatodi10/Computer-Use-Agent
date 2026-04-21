from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, LargeBinary, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class UserMessage(Base):
    """Stores user-facing chat history. Managed by SQLChatMessageHistory."""

    __tablename__ = "user_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str | None] = mapped_column(Text)
    message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (Index("ix_user_messages_session_id", "session_id"),)


class AgentMessage(Base):
    """Stores agent-to-agent chat history. Managed by SQLChatMessageHistory.
    The agent name is encoded in the message JSON under the 'name' key."""

    __tablename__ = "agent_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str | None] = mapped_column(Text)
    message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (Index("ix_agent_messages_session_id", "session_id"),)


class Checkpoint(Base):
    """LangGraph checkpointer state snapshots. Managed by AsyncSqliteSaver.
    Schema must match langgraph.checkpoint.sqlite exactly."""

    __tablename__ = "checkpoints"

    thread_id: Mapped[str] = mapped_column(Text, primary_key=True)
    checkpoint_ns: Mapped[str] = mapped_column(
        Text, primary_key=True, server_default=""
    )
    checkpoint_id: Mapped[str] = mapped_column(Text, primary_key=True)
    parent_checkpoint_id: Mapped[str | None] = mapped_column(Text)
    type: Mapped[str | None] = mapped_column(Text)
    checkpoint: Mapped[bytes | None] = mapped_column(LargeBinary)
    meta: Mapped[bytes | None] = mapped_column("metadata", LargeBinary)


class CheckpointWrite(Base):
    """LangGraph checkpointer pending writes. Managed by AsyncSqliteSaver.
    Schema must match langgraph.checkpoint.sqlite exactly."""

    __tablename__ = "writes"

    thread_id: Mapped[str] = mapped_column(Text, primary_key=True)
    checkpoint_ns: Mapped[str] = mapped_column(
        Text, primary_key=True, server_default=""
    )
    checkpoint_id: Mapped[str] = mapped_column(Text, primary_key=True)
    task_id: Mapped[str] = mapped_column(Text, primary_key=True)
    idx: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str | None] = mapped_column(Text)
    value: Mapped[bytes | None] = mapped_column(LargeBinary)


class UserMemory(Base):
    """Global (not session-scoped) memories about the user. Schema matches
    langchain_community.vectorstores.SQLiteVec exactly so its runtime
    CREATE TABLE IF NOT EXISTS is a no-op against the Alembic-created table.

    The companion vec0 virtual table `user_memories_vec` and three mirror
    triggers are created by `database/vec_ddl.py` (invoked from the migration)
    and are intentionally outside ORM metadata.
    """

    __tablename__ = "user_memories"

    rowid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[bytes | None] = mapped_column("metadata", LargeBinary)
    text_embedding: Mapped[bytes | None] = mapped_column(LargeBinary)
