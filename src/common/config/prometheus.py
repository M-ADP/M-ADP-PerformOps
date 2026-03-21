from pydantic_settings import BaseSettings

from src.common.const.vault import VAULT_ENV_FILE


class _Settings(BaseSettings):
    prometheus_url: str

    class Config:
        env_file = VAULT_ENV_FILE
        env_file_encoding = "utf-8"
        extra = "ignore"


class PrometheusConfig:
    URL: str = _Settings().prometheus_url
