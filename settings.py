from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: SecretStr
    sqlite_db_path: Path = Path("app.db")
    user_name: str = "user"

    @property
    def sqlite_db_file(self) -> Path:
        path = self.sqlite_db_path
        return path if path.is_absolute() else BASE_DIR / path

    @property
    def database_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.sqlite_db_file.as_posix()}"

    @property
    def sync_database_url(self) -> str:
        return f"sqlite:///{self.sqlite_db_file.as_posix()}"


settings = Settings()
