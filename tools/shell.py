"""Lightweight shell tool.

We don't use `langchain.agents.middleware.ShellToolMiddleware` because it stores
non-serializable process state (`Send` objects) on the agent state, which the
SQLite checkpointer cannot persist. Each call here is an independent subprocess
with no shared state — simpler, checkpointer-friendly, and still gated by
`CriticalShellInterruptMiddleware` via the tool name `shell`.
"""

from __future__ import annotations

import asyncio

from langchain_core.tools import BaseTool, tool

from settings import settings

MAX_OUTPUT_CHARS = 20_000
DEFAULT_TIMEOUT_SEC = 120


def _argv_for(shell_exe: str, command: str) -> list[str]:
    name = shell_exe.lower().rstrip(".exe")
    if name in ("powershell", "pwsh"):
        return [shell_exe, "-NoProfile", "-NonInteractive", "-Command", command]
    if name == "cmd":
        return [shell_exe, "/c", command]
    # bash / sh / zsh / fish etc.
    return [shell_exe, "-c", command]


def _truncate(text: str, label: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    omitted = len(text) - MAX_OUTPUT_CHARS
    return f"{text[:MAX_OUTPUT_CHARS]}\n[{label} truncated, {omitted} chars omitted]"


def build_shell_tool() -> list[BaseTool]:
    if not settings.shell_enabled:
        return []

    root = str(settings.agent_workspace)
    shell_exe = settings.shell_command

    @tool("shell")
    async def shell(command: str) -> str:
        """Execute a command in the workspace shell and return its output.

        Returns a formatted string with the command, stdout, stderr (if any),
        and exit code. The working directory is the agent workspace. Do not
        run interactive commands (editors, REPLs, `sudo` with password
        prompt) — they will hang and time out. Destructive or networked
        commands will trigger a human approval prompt."""
        argv = _argv_for(shell_exe, command)
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=root,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=DEFAULT_TIMEOUT_SEC
            )
        except asyncio.TimeoutError:
            proc.kill()
            try:
                await proc.wait()
            except Exception:
                pass
            return (
                f"$ {command}\n"
                f"[timed out after {DEFAULT_TIMEOUT_SEC}s; process killed]"
            )

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        parts: list[str] = [f"$ {command}"]
        if stdout.strip():
            parts.append(_truncate(stdout, "stdout"))
        if stderr.strip():
            parts.append("[stderr]")
            parts.append(_truncate(stderr, "stderr"))
        parts.append(f"[exit code: {proc.returncode}]")
        return "\n".join(parts)

    return [shell]
