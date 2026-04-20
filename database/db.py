from database.chats import AgentChatRepository, UserChatRepository
from database.connection import engine


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
