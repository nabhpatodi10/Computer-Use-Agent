from langchain_core.tools import BaseTool, tool

from database.memories import UserMemoryRepository


def build_memory_tools(repo: UserMemoryRepository) -> list[BaseTool]:
    """Build `@tool`-decorated memory ops over a shared repository instance.
    Each factory call closes over `repo`, so every tool uses the same
    SQLiteVec connection + OllamaEmbeddings client."""

    @tool
    async def add_memory(content: str, category: str | None = None) -> str:
        """Save a new memory about the user. Use for stable facts,
        preferences, goals, or ongoing project context that will be useful
        in future conversations. `category` is a short free-form tag like
        'preferences', 'facts', 'projects'. Returns the memory ID.
        Duplicates are detected and deduplicated automatically."""
        result = await repo.add(content, category)
        return f"Saved memory #{result['id']}: {result['text']}"

    @tool
    async def search_memories(query: str, limit: int = 5) -> str:
        """Semantic search over saved memories. Use when the user's
        request might benefit from prior context. Returns up to `limit`
        memories ranked by similarity (lower distance = more similar)."""
        hits = await repo.search(query, limit)
        if not hits:
            return "No memories found."
        lines = []
        for doc, score in hits:
            meta = doc.metadata or {}
            category = meta.get("category")
            tag = f" [{category}]" if category else ""
            lines.append(f"(distance={score:.3f}){tag}: {doc.page_content}")
        return "\n".join(lines)

    @tool
    async def list_memories(category: str | None = None, limit: int = 50) -> str:
        """List recent memories (most recently updated first). Optionally
        filter by category. Use when the user asks what's stored, or you
        need to audit the full set."""
        rows = await repo.list_all(category=category, limit=limit)
        if not rows:
            return "No memories saved."
        lines = []
        for r in rows:
            meta = r["metadata"] or {}
            category_ = meta.get("category")
            tag = f" [{category_}]" if category_ else ""
            lines.append(f"#{r['id']}{tag}: {r['text']}")
        return "\n".join(lines)

    @tool
    async def edit_memory(
        memory_id: int,
        content: str,
        category: str | None = None,
    ) -> str:
        """Update an existing memory. Use when you learn a memory is
        outdated or wrong. Pass the memory ID from a prior
        search/list call."""
        result = await repo.edit(memory_id, content, category)
        return f"Updated memory #{result['id']}: {result['text']}"

    @tool
    async def delete_memory(memory_id: int) -> str:
        """Permanently remove a memory. Use when the user asks you to
        forget something, or when a memory is no longer relevant."""
        ok = await repo.delete(memory_id)
        return (
            f"Deleted memory #{memory_id}." if ok else f"Memory #{memory_id} not found."
        )

    return [add_memory, search_memories, list_memories, edit_memory, delete_memory]
