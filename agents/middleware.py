from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from typing_extensions import NotRequired, TypedDict

from agents.router import model_router


class ModelSelectionState(TypedDict):
    selected_model_tier: NotRequired[str]


class ModelSelectionMiddleware(AgentMiddleware):
    """Chooses between fast_model and smart_model using selector_model.

    Routes once per user turn: when the latest message is a HumanMessage, the selector
    is asked to pick fast vs smart. The choice is stored in state so tool-call follow-up
    steps within the same turn stay on the chosen model.
    """

    state_schema = ModelSelectionState

    def __init__(
        self,
        selector_model: BaseChatModel,
        fast_model: BaseChatModel,
        smart_model: BaseChatModel,
    ) -> None:
        super().__init__()
        self._selector = selector_model
        self._fast = fast_model
        self._smart = smart_model

    async def awrap_model_call(
        self,
        request: Any,
        handler: Callable[[Any], Awaitable[Any]],
    ) -> Any:
        state = request.state
        messages = state.get("messages", [])
        tier: str | None = state.get("selected_model_tier")

        last_is_human = bool(messages) and isinstance(messages[-1], HumanMessage)
        if tier is None or last_is_human:
            tier = await model_router(self._selector, messages)

        request.model = self._smart if tier == "smart" else self._fast

        response = await handler(request)

        if isinstance(response, dict):
            response.setdefault("selected_model_tier", tier)
        return response
