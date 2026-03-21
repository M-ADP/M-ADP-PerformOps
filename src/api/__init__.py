from fastapi import FastAPI

from src.api.performops import performops_router


def register_routers(app: FastAPI) -> None:
    app.include_router(performops_router)


def create_app() -> FastAPI:
    app = FastAPI()
    register_routers(app)
    return app