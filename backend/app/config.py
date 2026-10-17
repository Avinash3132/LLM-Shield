"""Application Settings for LLMShield."""

from pathlib import Path
from typing import List, Any
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    """Pydantic settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=(str(PROJECT_ROOT / ".env"), str(BACKEND_DIR / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "LLMShield Gauntlet Backend"
    app_env: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # AI Configuration
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.7-flash"

    # ArmorIQ Configuration
    armoriq_api_key: str = ""
    armoriq_endpoint: str = "https://api.armoriq.ai/v1"
    armoriq_agent_id: str = "agent_llm_shield_01"
    armoriq_environment: str = "sandbox"

    # Sandboxes Storage
    data_dir: Path = BACKEND_DIR / "data"
    file_vault_dir: Path = BACKEND_DIR / "data" / "file_vault"
    crm_data_path: Path = BACKEND_DIR / "data" / "crm" / "customers.json"
    email_outbox_path: Path = BACKEND_DIR / "data" / "email_outbox" / "outbox.json"

    @classmethod
    def _resolve_path(cls, p: Path | str) -> Path:
        path_obj = Path(p)
        if not path_obj.is_absolute():
            return (BACKEND_DIR / path_obj).resolve()
        return path_obj

    def model_post_init(self, __context: Any) -> None:
        self.data_dir = self._resolve_path(self.data_dir)
        self.file_vault_dir = self._resolve_path(self.file_vault_dir)
        self.crm_data_path = self._resolve_path(self.crm_data_path)
        self.email_outbox_path = self._resolve_path(self.email_outbox_path)

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_gemini_configured(self) -> bool:
        return bool(self.gemini_api_key and not self.gemini_api_key.startswith("your_"))

    @property
    def is_armoriq_configured(self) -> bool:
        return bool(self.armoriq_api_key and not self.armoriq_api_key.startswith("your_"))


settings = Settings()
