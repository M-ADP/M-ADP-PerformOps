from pydantic_settings import BaseSettings


class _Settings(BaseSettings):
    prometheus_url: str

    class Config:
        env_file = ".env"
        extra = "ignore"


class PrometheusConfig:
    URL: str = _Settings().prometheus_url
