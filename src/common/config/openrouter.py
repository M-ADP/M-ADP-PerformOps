from pydantic_settings import BaseSettings


class _Settings(BaseSettings):
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    class Config:
        env_file = ".env"
        extra = "ignore"


_settings = _Settings()


class OpenRouterConfig:
    API_KEY: str = _settings.openrouter_api_key
    BASE_URL: str = _settings.openrouter_base_url
