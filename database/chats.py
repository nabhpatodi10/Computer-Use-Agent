import re
from abc import ABC, abstractmethod

from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage
from sqlalchemy.ext.asyncio import AsyncEngine

from settings import settings


def _normalize_name(name: str) -> str:
    """OpenAI requires message.name to match ^[^\\s<|\\\\/>]+$ — strip disallowed chars."""
    return re.sub(r"[\s<|\\/>]+", "_", name.strip())


class BaseChatRepository(ABC):
    @abstractmethod
    async def add_message(self, message: BaseMessage) -> None: ...

    @abstractmethod
    async def get_messages(self) -> list[BaseMessage]: ...


class UserChatRepository(BaseChatRepository):
    def __init__(self, session_id: str, engine: AsyncEngine) -> None:
        self._user_name = _normalize_name(settings.user_name)
        self._history = SQLChatMessageHistory(
            session_id=session_id,
            connection=engine,
            async_mode=True,
            table_name="user_messages",
        )

    async def add_message(self, message: BaseMessage) -> None:
        if isinstance(message, HumanMessage):
            message.name = self._user_name
        await self._history.aadd_messages([message])

    async def get_messages(self) -> list[BaseMessage]:
        return await self._history.aget_messages()


class AgentChatRepository(BaseChatRepository):
    def __init__(self, session_id: str, engine: AsyncEngine) -> None:
        self._history = SQLChatMessageHistory(
            session_id=session_id,
            connection=engine,
            async_mode=True,
            table_name="agent_messages",
        )

    async def add_message(self, message: BaseMessage, agent_name: str | None = None) -> None:
        if message.name is None and agent_name is None:
            raise ValueError("Agent name must be provided if message does not have a name.")
        if agent_name is not None:
            message.name = _normalize_name(agent_name)
        await self._history.aadd_messages([message])

    async def get_messages(self, agent_name: str | None = None) -> list[BaseMessage]:
        messages = await self._history.aget_messages()
        if agent_name is not None:
            return [m for m in messages if m.name == agent_name]
        return messages
