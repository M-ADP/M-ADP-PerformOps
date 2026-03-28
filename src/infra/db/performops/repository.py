from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.id_generator import IdGenerator
from src.common.schema import CursorPage, CursorRequest
from src.core.performops.model import (
    ActionState,
    Performops,
    PerformOpsAction,
    PerformOpsResult,
)
from src.core.performops.repository import PerformopsRepository
from src.infra.db.performops.model import (
    PerformOps,
    PerformOpsAction as PerformOpsActionORM,
)


class PerformopsRepositoryImpl(PerformopsRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_project_id(
        self, project_id: int, cursor_request: CursorRequest
    ) -> CursorPage[Performops]:
        query = select(PerformOps).where(PerformOps.project_id == project_id)

        if cursor_request.cursor is not None:
            query = query.where(PerformOps.id > cursor_request.cursor)

        query = query.order_by(PerformOps.id).limit(cursor_request.size + 1)

        result = await self.session.execute(query)
        rows = result.scalars().all()

        has_next = len(rows) > cursor_request.size
        items = [self._to_domain(row) for row in rows[: cursor_request.size]]

        return CursorPage(items=items, has_next=has_next)

    async def save(self, performops_result: PerformOpsResult) -> Performops:
        model = self._to_model(performops_result)
        self.session.add(model)
        await self.session.flush()
        return self._to_domain(model)

    async def get_actions_by_ids(self, action_ids: List[int]) -> List[PerformOpsAction]:
        """요청된 action_ids 순서를 유지하여 반환"""
        query = select(PerformOpsActionORM).where(
            PerformOpsActionORM.id.in_(action_ids)
        )
        result = await self.session.execute(query)
        rows = {row.id: row for row in result.scalars().all()}

        # 요청한 ids 순서(생성 계획 순서) 유지
        return [
            self._action_to_domain(rows[action_id])
            for action_id in action_ids
            if action_id in rows
        ]

    async def update_action_state(self, action_id: int, state: ActionState) -> None:
        query = select(PerformOpsActionORM).where(PerformOpsActionORM.id == action_id)
        result = await self.session.execute(query)
        action = result.scalar_one_or_none()
        if action:
            action.state = state.value

    def _action_to_domain(self, a: PerformOpsActionORM) -> PerformOpsAction:
        return PerformOpsAction(
            id=a.id,
            performops_id=a.performops_id,
            action=a.action,
            state=a.state,
            http_method=a.http_method,
            http_path=a.http_path,
            http_body=a.http_body,
            created_at=a.created_at,
        )

    def _to_domain(self, model: PerformOps) -> Performops:
        return Performops(
            id=model.id,
            project_id=model.project_id,
            app_deployment_name=model.app_deployment_name,
            summary=model.summary,
            influence=model.influence,
            cause=model.cause,
            severity=model.severity,
            created_at=model.created_at,
            actions=[self._action_to_domain(a) for a in model.actions],
        )

    def _to_model(self, performops_result: PerformOpsResult) -> PerformOps:
        actions = [
            PerformOpsActionORM(
                id=IdGenerator.generate_sonyflake_id(),
                action=plan_action.action,
                state=ActionState.PENDING.value,
                http_method=plan_action.http_method or None,
                http_path=plan_action.http_path or None,
                http_body=plan_action.http_body or None,
            )
            for plan_action in performops_result.plan.actions
        ]
        return PerformOps(
            id=IdGenerator.generate_sonyflake_id(),
            project_id=performops_result.project_id,
            app_deployment_name=performops_result.app_deployment_name,
            summary=performops_result.summary_text,
            severity=performops_result.severity,
            influence=performops_result.analysis_result.resource.traffic.basis,
            cause=performops_result.analysis_result.result,
            actions=actions,
        )
