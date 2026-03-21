from pydantic_settings import BaseSettings


class _Settings(BaseSettings):
    resource_manager_url: str

    class Config:
        env_file = ".env"


class ResourceManagerConfig:
    URL: str = _Settings().resource_manager_url
