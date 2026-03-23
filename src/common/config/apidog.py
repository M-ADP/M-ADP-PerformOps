from pydantic_settings import BaseSettings

from src.common.const.vault import VAULT_ENV_FILE


class _Settings(BaseSettings):
    apidog_token: str
    apidog_project_id: str

    class Config:
        env_file = VAULT_ENV_FILE
        env_file_encoding = "utf-8"
        extra = "ignore"


class ApidogConfig:
    TOKEN: str = _Settings().apidog_token
    PROJECT_ID: str = _Settings().apidog_project_id
