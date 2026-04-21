from database.chats import AgentChatRepository, UserChatRepository
from database.connection import engine, get_memory_repo


class DB:
    def __init__(self, session_id: str) -> None:
        self.user_chats = UserChatRepository(
            session_id=session_id,
            engine=engine,
        )
        self.agent_chats = AgentChatRepository(
            session_id=session_id,
            engine=engine,
        )
        # Memories are global (not session-scoped) but accessed via the facade
        # for a single entry point.
        self.memories = get_memory_repo()
