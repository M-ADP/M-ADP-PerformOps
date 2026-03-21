from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    prometheus_url: str
    resource_manager_url: str
    sentry_auth_token: str
    sentry_organization_slug: str

    class Config:
        env_file = ".env"


settings = Settings()
