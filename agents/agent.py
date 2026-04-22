from langchain.agents import create_agent
from langchain.agents.middleware import (
    SummarizationMiddleware,
    TodoListMiddleware,
)
from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.types import Command
from deepagents.backends import FilesystemBackend
from deepagents.middleware import (
    FilesystemMiddleware,
    MemoryMiddleware,
    SkillsMiddleware,
)
from deepagents.middleware.patch_tool_calls import PatchToolCallsMiddleware

from agents.middleware import (
    CriticalShellInterruptMiddleware,
    ModelSelectionMiddleware,
)
from tools import build_memory_tools, build_shell_tool, build_web_search_tools
from prompts import chatbot_prompt, memory_prompt
from database import DB, close_connections, get_checkpointer
from database.connection import get_memory_repo
from settings import settings

_agent = None


def _build_backend() -> FilesystemBackend:
    settings.agent_workspace.mkdir(parents=True, exist_ok=True)
    return FilesystemBackend(
        root_dir=str(settings.agent_workspace),
        virtual_mode=True,
    )


def _build_middleware_stack(backend, fast_model, smart_model, selector_model):
    """Compose the middleware stack manually (subagent middleware omitted so the
    user can design a custom subagent system later). Order mirrors deepagents'
    base stack for known-good ordering: tool-providing middlewares first,
    summarization next, patch-tool-calls, user middleware, tail memory."""
    stack = [TodoListMiddleware()]

    if settings.skills_sources:
        stack.append(SkillsMiddleware(backend=backend, sources=settings.skills_sources))

    stack.append(FilesystemMiddleware(backend=backend))

    if settings.shell_enabled:
        # Shell tool itself is a plain tool (see tools/shell.py), not a
        # middleware — ShellToolMiddleware stores non-serializable process
        # state which breaks SQLite checkpointing. This middleware only gates
        # calls to it for critical-command approval.
        stack.append(
            CriticalShellInterruptMiddleware(
                critical_patterns=settings.shell_critical_patterns,
            )
        )

    stack.append(
        SummarizationMiddleware(model=fast_model, trigger=("fraction", 0.85))
    )
    stack.append(PatchToolCallsMiddleware())

    # Our custom per-turn model selector (uses request.state, swaps request.model).
    stack.append(
        ModelSelectionMiddleware(
            selector_model=selector_model,
            fast_model=fast_model,
            smart_model=smart_model,
        )
    )

    # AGENTS.md-style static memory (different from our user-memory tools);
    # lives near the tail so it doesn't interact with summarization.
    if settings.agents_md_sources:
        stack.append(
            MemoryMiddleware(backend=backend, sources=settings.agents_md_sources)
        )

    return stack


async def get_agent():
    global _agent
    if _agent is not None:
        return _agent

    selector_model = init_chat_model(settings.selector_model)
    fast_model = init_chat_model(settings.fast_model)
    smart_model = init_chat_model(settings.smart_model)

    backend = _build_backend()
    middleware = _build_middleware_stack(
        backend=backend,
        fast_model=fast_model,
        smart_model=smart_model,
        selector_model=selector_model,
    )

    tools = [
        *build_memory_tools(get_memory_repo()),
        *build_web_search_tools(),
        *build_shell_tool(),
    ]

    _agent = create_agent(
        model=fast_model,  # default; ModelSelectionMiddleware swaps per turn
        tools=tools,
        system_prompt=f"{chatbot_prompt}\n\n{memory_prompt}",
        middleware=middleware,
        checkpointer=await get_checkpointer(),
        name="chatbot-agent",
    )
    return _agent


def _prompt_user_for_shell_decision(payload: dict) -> dict:
    """Default CLI-based approval prompt for a critical shell command.
    Override by passing `approver` to `invoke()` if embedding in a UI."""
    command = payload.get("command", "")
    print()
    print("=" * 70)
    print("AGENT requests approval to run a critical shell command:")
    print(f"  {command}")
    print("=" * 70)
    choice = input("Approve? [y/N] (or type a rejection reason): ").strip()
    if choice.lower() in ("y", "yes"):
        return {"decision": "approve"}
    return {
        "decision": "reject",
        "reason": choice if choice and choice.lower() not in ("n", "no") else "rejected",
    }


async def invoke(
    session_id: str,
    user_input: str,
    approver=_prompt_user_for_shell_decision,
) -> BaseMessage:
    db = DB(session_id=session_id)
    user_msg = HumanMessage(content=user_input)
    await db.user_chats.add_message(user_msg)

    agent = await get_agent()
    config = {"configurable": {"thread_id": session_id}}

    agent_input: object = {"messages": [user_msg]}
    while True:
        result = await agent.ainvoke(agent_input, config=config)
        interrupts = result.get("__interrupt__")
        if not interrupts:
            break
        # Handle the (first) interrupt. langgraph pauses the graph; we resume
        # via Command(resume=<value>).
        payload = interrupts[0].value
        decision = approver(payload)
        agent_input = Command(resume=decision)

    response: BaseMessage = result["messages"][-1]
    response.name = "chatbot-agent"
    await db.user_chats.add_message(response)
    return response


async def close() -> None:
    global _agent
    _agent = None
    await close_connections()
