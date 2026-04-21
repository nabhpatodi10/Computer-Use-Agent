from pathlib import Path

_DIR = Path(__file__).parent


def _load(name: str) -> str:
    return (_DIR / f"{name}.md").read_text(encoding="utf-8").strip()


chatbot_prompt = _load("chatbot")
model_router_prompt = _load("model_router")
memory_prompt = _load("memory")

__all__ = ["chatbot_prompt", "model_router_prompt", "memory_prompt"]
