from pydantic_settings import BaseSettings

from src.common.const.vault import VAULT_ENV_FILE


class _Settings(BaseSettings):
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    class Config:
        env_file = VAULT_ENV_FILE
        env_file_encoding = "utf-8"
        extra = "ignore"


_settings = _Settings()


class OpenRouterConfig:
    API_KEY: str = _settings.openrouter_api_key
    BASE_URL: str = _settings.openrouter_base_url
