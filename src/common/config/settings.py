from pydantic_settings import BaseSettings

from src.common.const.vault import VAULT_ENV_FILE


class _SonyflakeSettings(BaseSettings):
    machine_id: int = 1

    class Config:
        env_file = VAULT_ENV_FILE
        env_file_encoding = "utf-8"
        extra = "ignore"


def get_sonyflake_config() -> _SonyflakeSettings:
    return _SonyflakeSettings()
