from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage

from prompts import model_router_prompt
from agents.schema import ModelRouterOutput


async def model_router(selector_model: BaseChatModel, messages: list[BaseMessage]) -> str:
    """Run the selector model against the conversation and return 'fast' or 'smart'."""
    system_message = SystemMessage(content=model_router_prompt)
    response = await (
        selector_model.with_structured_output(ModelRouterOutput).ainvoke(
            [system_message] + list(messages)
        )
    )
    selected = (response.get("model") or "").lower()
    if "smart" in selected:
        return "smart"
    return "fast"
