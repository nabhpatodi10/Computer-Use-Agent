"""Unified web-search tool with provider fallback.

Primary: Tavily (LLM-optimized results, returns summarized content).
Fallback: Exa (semantic search, good for research queries).

If both are configured, Tavily is tried first; on any exception, Exa is used.
If only one is configured, that one is used directly.
If neither is configured, `build_web_search_tools()` returns an empty list
(no tool is exposed to the agent)."""

from __future__ import annotations

import logging
import os
from typing import Any

from langchain_core.tools import BaseTool, tool

from settings import settings

logger = logging.getLogger(__name__)


def _build_tavily() -> Any | None:
    if settings.tavily_api_key is None:
        return None
    # langchain_tavily's TavilySearch reads TAVILY_API_KEY from os.environ.
    # settings.load_dotenv() already populated it from .env; re-export to be safe.
    os.environ.setdefault(
        "TAVILY_API_KEY", settings.tavily_api_key.get_secret_value()
    )
    from langchain_tavily import TavilySearch

    return TavilySearch(max_results=5, topic="general", search_depth="advanced")


def _build_exa() -> Any | None:
    if settings.exa_api_key is None:
        return None
    from langchain_exa import ExaSearchResults

    return ExaSearchResults(exa_api_key=settings.exa_api_key.get_secret_value())


def _format_tavily(result: Any) -> str:
    """Tavily returns a dict with 'results' list + optional 'answer'."""
    if not isinstance(result, dict):
        return str(result)
    lines: list[str] = []
    if ans := result.get("answer"):
        lines.append(f"Answer: {ans}")
    for i, r in enumerate(result.get("results", []), start=1):
        title = r.get("title", "")
        url = r.get("url", "")
        content = (r.get("content") or "").strip()
        lines.append(f"[{i}] {title}\n{url}\n{content}")
    return "\n\n".join(lines) if lines else "No results."


def _format_exa(result: Any) -> str:
    """Exa returns a list[dict] or a str."""
    if isinstance(result, str):
        return result
    if not isinstance(result, list):
        return str(result)
    lines: list[str] = []
    for i, r in enumerate(result, start=1):
        if not isinstance(r, dict):
            lines.append(f"[{i}] {r}")
            continue
        title = r.get("title", "")
        url = r.get("url", "")
        text = (r.get("text") or r.get("summary") or "").strip()
        lines.append(f"[{i}] {title}\n{url}\n{text}")
    return "\n\n".join(lines) if lines else "No results."


def build_web_search_tools() -> list[BaseTool]:
    tavily = _build_tavily()
    exa = _build_exa()

    if tavily is None and exa is None:
        return []

    provider_note = "Tavily (primary) with Exa fallback" if (tavily and exa) else (
        "Tavily only" if tavily else "Exa only"
    )
    logger.info("web_search tool enabled (%s).", provider_note)

    @tool
    async def web_search(query: str) -> str:
        """Search the web for up-to-date information.

        Returns a plain-text list of results (title, URL, excerpt). Use for
        anything requiring current information the model wouldn't reliably
        know: news, recent events, docs for external libraries, verification
        of facts.
        """
        if tavily is not None:
            try:
                raw = await tavily.ainvoke({"query": query})
                return _format_tavily(raw)
            except Exception as exc:
                if exa is None:
                    raise
                logger.warning("Tavily failed (%s); falling back to Exa.", exc)

        # Either Tavily wasn't configured or it failed and Exa is the fallback.
        if exa is not None:
            raw = await exa.ainvoke({"query": query})
            return _format_exa(raw)

        raise RuntimeError("No web-search provider available.")

    return [web_search]
