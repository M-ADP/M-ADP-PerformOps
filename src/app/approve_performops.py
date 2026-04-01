import json
import logging
from typing import List

from fastapi import Depends

from src.app.base_usecase import BaseUseCase
from src.common.config.resource_manager import ResourceManagerConfig
from src.core.performops.core import PerformOpsCore
from src.core.performops.model import ActionState, Performops, PerformOpsAction
from src.core.uow import UnitOfWork
from src.deps.get_performops_core import get_performops_core
from src.deps.get_uow import get_uow
from src.infra.client.http_requester import HttpRequester

logger = logging.getLogger(__name__)

_METHOD_MAP = {
    "GET": HttpRequester.get,
    "POST": HttpRequester.post,
    "PATCH": HttpRequester.patch,
    "PUT": HttpRequester.put,
    "DELETE": HttpRequester.delete,
}


class ApprovePerformopsUseCase(BaseUseCase):
    def __init__(
        self,
        uow: UnitOfWork = Depends(get_uow),
        performops_core: PerformOpsCore = Depends(get_performops_core),
    ):
        self.uow = uow
        self.performops_core = performops_core
        self.requester = HttpRequester()
        self.base_url = ResourceManagerConfig.URL

    async def __call__(
        self,
        performops_id: int,
        action_ids: List[int],
    ) -> Performops:
        actions = await self.uow.performops.get_actions_by_ids(action_ids)

        original = await self._get_performops(performops_id)
        context = {
            "project_id": original.project_id,
            "app_deployment_name": original.app_deployment_name,
        }

        for action in actions:
            await self._execute_action(action, context)

        new_result = await self.performops_core.start(
            project_id=original.project_id,
            app_deployment_name=original.app_deployment_name,
        )
        saved = await self.uow.performops.save(new_result)

        return saved

    async def _execute_action(self, action: PerformOpsAction, context: dict) -> None:
        method = (action.http_method or "").upper()
        path = action.http_path or ""

        if not method or not path:
            logger.warning(
                f"[approve] action_id={action.id} http info missing, skipping"
            )
            await self.uow.performops.update_action_state(action.id, ActionState.FAILED)
            return

        path = self._substitute_path(path, context)
        if not path:
            logger.warning(
                f"[approve] action_id={action.id} path variable substitution failed, skipping"
            )
            await self.uow.performops.update_action_state(action.id, ActionState.FAILED)
            return

        url = self.base_url.rstrip("/") + path
        body = json.loads(action.http_body) if action.http_body else None

        try:
            caller = _METHOD_MAP.get(method)
            if caller is None:
                raise ValueError(f"unsupported HTTP method: {method}")

            if method in ("POST", "PATCH", "PUT"):
                await caller(self.requester, url=url, body=body)
            else:
                await caller(self.requester, url=url)

            await self.uow.performops.update_action_state(
                action.id, ActionState.EXECUTED
            )
            logger.info(f"[approve] action_id={action.id} executed: {method} {path}")

        except Exception as e:
            logger.error(f"[approve] action_id={action.id} execution failed: {e}")
            await self.uow.performops.update_action_state(action.id, ActionState.FAILED)

    def _substitute_path(self, path: str, context: dict) -> str:
        replacements = {
            "{project-id}": str(context.get("project_id", "")),
            "{project_id}": str(context.get("project_id", "")),
            "{name}": context.get("app_deployment_name", ""),
            "{app_deployment_name}": context.get("app_deployment_name", ""),
            "{app-name}": context.get("app_deployment_name", ""),
            "{dns_id}": str(context.get("dns_id", "")),
            "{dns_name}": context.get("dns_name", ""),
        }

        for placeholder, value in replacements.items():
            if placeholder in path:
                if not value:
                    logger.warning(f"[approve] missing value for {placeholder}")
                    return ""
                path = path.replace(placeholder, value)

        if "{" in path or "}" in path:
            logger.warning(f"[approve] unresolved path variables remaining: {path}")
            return ""

        return path

    async def _get_performops(self, performops_id: int) -> Performops:
        from sqlalchemy import select
        from src.infra.db.performops.model import PerformOps as PerformOpsORM
        from src.infra.db.uow import SqlAlchemyUnitOfWork

        uow: SqlAlchemyUnitOfWork = self.uow  # type: ignore
        result = await uow.session.execute(
            select(PerformOpsORM).where(PerformOpsORM.id == performops_id)
        )
        orm = result.scalar_one()
        return self.uow.performops._to_domain(orm)  # type: ignore
