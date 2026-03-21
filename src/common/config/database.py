from pydantic_settings import BaseSettings

from src.common.const.vault import VAULT_ENV_FILE


class _Settings(BaseSettings):
    database_url: str

    class Config:
        env_file = VAULT_ENV_FILE
        env_file_encoding = "utf-8"
        extra = "ignore"


class DatabaseConfig:
    URL: str = _Settings().database_url
