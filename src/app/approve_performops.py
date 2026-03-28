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
        # 1. action_ids 순서대로 actions 조회
        actions = await self.uow.performops.get_actions_by_ids(action_ids)

        # 2. 순서대로 Resource Manager 호출
        for action in actions:
            await self._execute_action(action)

        await self.uow.commit()

        # 3. analyzer + planner 재실행 → 새 PerformOps 저장
        # performops_id로 원본 performops 정보 조회
        original = await self._get_performops(performops_id)
        new_result = await self.performops_core.start(
            project_id=original.project_id,
            app_deployment_name=original.app_deployment_name,
        )
        saved = await self.uow.performops.save(new_result)
        await self.uow.commit()

        return saved

    async def _execute_action(self, action: PerformOpsAction) -> None:
        method = (action.http_method or "").upper()
        path = action.http_path or ""

        if not method or not path:
            logger.warning(f"[approve] action_id={action.id} http 정보 없음, 건너뜀")
            await self.uow.performops.update_action_state(action.id, ActionState.FAILED)
            return

        url = self.base_url.rstrip("/") + path
        body = json.loads(action.http_body) if action.http_body else None

        try:
            caller = _METHOD_MAP.get(method)
            if caller is None:
                raise ValueError(f"지원하지 않는 HTTP method: {method}")

            if method in ("POST", "PATCH", "PUT"):
                await caller(self.requester, url=url, body=body)
            else:
                await caller(self.requester, url=url)

            await self.uow.performops.update_action_state(
                action.id, ActionState.EXECUTED
            )
            logger.info(f"[approve] action_id={action.id} 실행 완료: {method} {path}")

        except Exception as e:
            logger.error(f"[approve] action_id={action.id} 실행 실패: {e}")
            await self.uow.performops.update_action_state(action.id, ActionState.FAILED)

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
