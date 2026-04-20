from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, Text, func
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
