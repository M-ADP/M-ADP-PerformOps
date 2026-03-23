import logging
from contextlib import asynccontextmanager
from json import JSONDecodeError

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.api.performops import performops_router
from src.core.user_action_store import UserActionStore
from src.infra.client.apidog_client import ApidogClient

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        actions = await ApidogClient().fetch_user_actions()
        UserActionStore.set(actions)
    except Exception as e:
        logger.warning(f"[startup] apidog user action 로드 실패: {e}")
    yield


def register_routers(app: FastAPI) -> None:
    app.include_router(performops_router)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(JSONDecodeError)
    async def json_decode_exception_handler(request: Request, exc: JSONDecodeError):
        return JSONResponse(status_code=500, content={"detail": f"LLM 응답 파싱 실패: {exc}"})

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content={"detail": str(exc)})


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    register_routers(app)
    register_exception_handlers(app)
    return app
