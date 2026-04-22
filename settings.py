from pathlib import Path

from dotenv import load_dotenv
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent

# Ensure provider API keys from .env are in os.environ so init_chat_model can read them.
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: SecretStr
    sqlite_db_path: Path = Path("app.db")
    user_name: str = "user"
    agent_workspace_path: Path = Path("agent_workspace")

    # Model tiers. Format: "provider:model" (e.g. "openai:gpt-4o-mini",
    # "anthropic:claude-sonnet-4-6", "google_genai:gemini-2.0-flash").
    selector_model: str = "openai:gpt-4o-mini"
    fast_model: str = "openai:gpt-5.4-nano"
    smart_model: str = "openai:gpt-5.4-mini"

    # Embeddings (used for user-memory vector search).
    embedding_model: str = "qwen3-embedding:0.6b"
    ollama_base_url: str | None = None  # None -> langchain-ollama default http://localhost:11434
    embedding_dim: int = 1024

    # Optional: paths (relative to agent_workspace) for deepagents Skills /
    # AGENTS.md-style Memory middleware. Leave empty to disable those middlewares.
    skills_sources: list[str] = []
    agents_md_sources: list[str] = []

    # Web search providers. Configure whichever you have; the agent uses
    # Tavily as primary and falls back to Exa on error. Tool is only added
    # if at least one is set.
    tavily_api_key: SecretStr | None = None
    exa_api_key: SecretStr | None = None

    # Shell tool. Executes commands via deepagents/langchain ShellToolMiddleware.
    # HITL kicks in only for commands matching `shell_critical_patterns`.
    shell_enabled: bool = True
    shell_command: str = "powershell"  # "pwsh", "bash", "cmd", etc.
    shell_critical_patterns: list[str] = [
        r"\brm\s+[^\n]*-[rRfF]",
        r"\bsudo\b",
        r"\bchmod\b",
        r"\bchown\b",
        r"\bdel\s+[^\n]*[/\-][fFsSqQ]",
        r"\bformat\s+[a-zA-Z]:",
        r"\bshutdown\b",
        r"\breboot\b",
        r"\bgit\s+push\b",
        r"\bgit\s+reset\s+--hard",
        r"\bgit\s+clean\s+-[fdxFDX]",
        r"\bpip\s+install\b",
        r"\bnpm\s+install\b",
        r"\bcurl\s+[^\n]*\|\s*(sh|bash|pwsh|powershell)",
        r"\b(iwr|irm|Invoke-WebRequest|Invoke-RestMethod)\b[^\n]*\|\s*iex",
        r"\bRemove-Item\b[^\n]*-Recurse",
        r">\s*/dev/",
        r"\bdd\s+if=",
    ]

    @property
    def sqlite_db_file(self) -> Path:
        path = self.sqlite_db_path
        return path if path.is_absolute() else BASE_DIR / path

    @property
    def agent_workspace(self) -> Path:
        path = self.agent_workspace_path
        return path if path.is_absolute() else BASE_DIR / path

    @property
    def database_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.sqlite_db_file.as_posix()}"

    @property
    def sync_database_url(self) -> str:
        return f"sqlite:///{self.sqlite_db_file.as_posix()}"


settings = Settings()
