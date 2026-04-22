import re
from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.types import interrupt
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


class CriticalShellInterruptMiddleware(AgentMiddleware):
    """Intercepts shell tool calls; pauses for human approval only when the
    command matches one of the configured 'critical' regex patterns.

    Non-critical commands pass through without interruption. The caller
    (invoke()) is responsible for surfacing the interrupt and resuming the
    graph via `Command(resume={"decision": "approve"|"reject"})`.
    """

    def __init__(
        self,
        critical_patterns: list[str],
        tool_name: str = "shell",
    ) -> None:
        super().__init__()
        self._tool_name = tool_name
        self._patterns = [
            re.compile(p, re.IGNORECASE | re.MULTILINE) for p in critical_patterns
        ]

    def _is_critical(self, command: str) -> bool:
        if not command:
            return False
        return any(p.search(command) for p in self._patterns)

    async def awrap_tool_call(
        self,
        request: Any,
        handler: Callable[[Any], Awaitable[Any]],
    ) -> Any:
        call = request.tool_call
        if call.get("name") != self._tool_name:
            return await handler(request)

        command = (call.get("args") or {}).get("command") or ""
        if not self._is_critical(command):
            return await handler(request)

        # Pause the graph. The payload is what the caller sees via
        # result["__interrupt__"][0].value.
        response = interrupt(
            {
                "kind": "shell_critical_command",
                "tool": self._tool_name,
                "command": command,
                "message": "Agent wants to run a critical shell command. Approve?",
            }
        )

        decision = (
            response.get("decision") if isinstance(response, dict) else response
        )
        if decision == "approve":
            return await handler(request)

        # Reject (default): short-circuit with a ToolMessage the model can see.
        reason = (
            response.get("reason")
            if isinstance(response, dict)
            else "User rejected the command."
        )
        return ToolMessage(
            content=f"Command rejected by user. Reason: {reason}",
            tool_call_id=call.get("id", ""),
            status="error",
        )
