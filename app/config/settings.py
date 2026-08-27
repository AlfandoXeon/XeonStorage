from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "XeonStorage"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    default_language: str = "en"
    max_upload_size_mb: int = 1500
    session_secret: str = "CHANGE_ME_IN_PRODUCTION"

    database_url: str = "sqlite:///./data/xeonstorage.db"
    database_auth_token: str = ""

    storage_provider: str = "telegram"
    local_storage_path: str = "./data/files"
    cache_max_size_mb: int = 500
    cache_ttl_hours: int = 24

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_channel_id: str = ""
    telegram_api_base: str = "https://api.telegram.org"
    telegram_api_id: int = 0
    telegram_api_hash: str = ""
    telegram_session_string: str = ""
    telegram_storage_enabled: bool = True

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @property
    def resolved_telegram_chat_id(self) -> str:
        return self.telegram_channel_id or self.telegram_chat_id

@lru_cache
def get_settings() -> Settings:
    return Settings()
