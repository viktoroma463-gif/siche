from pathlib import Path
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict


def resolve_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


ROOT = resolve_root()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(ROOT / ".env", Path.cwd() / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    siche_deepseek_api_key: str = ""
    siche_deepseek_base_url: str = "https://api.deepseek.com"
    siche_deepseek_model: str = "deepseek-flash"
    siche_deepseek_timeout: float = 60.0
    siche_deepseek_max_tokens: int = 3000
    siche_history_limit: int = 12

    @property
    def llm_configured(self) -> bool:
        return bool((self.siche_deepseek_api_key or "").strip())


settings = Settings()
