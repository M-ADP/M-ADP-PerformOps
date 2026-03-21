from pydantic_settings import BaseSettings


class _Settings(BaseSettings):
    database_url: str

    class Config:
        env_file = ".env"


class DatabaseConfig:
    URL: str = _Settings().database_url
