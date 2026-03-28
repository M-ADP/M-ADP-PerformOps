from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.schema import CursorPage, CursorRequest
from src.core.performops.model import Performops, PerformOpsResult, PerformOpsAction
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

    def _to_domain(self, model: PerformOps) -> Performops:
        actions = [
            PerformOpsAction(
                id=a.id,
                performops_id=a.performops_id,
                action=a.action,
                state=a.state,
                http_method=a.http_method,
                http_path=a.http_path,
                http_body=a.http_body,
                created_at=a.created_at,
            )
            for a in model.actions
        ]
        return Performops(
            id=model.id,
            project_id=model.project_id,
            app_deployment_name=model.app_deployment_name,
            summary=model.summary,
            influence=model.influence,
            cause=model.cause,
            severity=model.severity,
            created_at=model.created_at,
            actions=actions,
        )

    def _to_model(self, performops_result: PerformOpsResult) -> PerformOps:
        actions = [
            PerformOpsActionORM(
                action=plan_action.action,
                state="pending",
                http_method=plan_action.http_method or None,
                http_path=plan_action.http_path or None,
                http_body=plan_action.http_body or None,
            )
            for plan_action in performops_result.plan.actions
        ]
        return PerformOps(
            project_id=performops_result.project_id,
            app_deployment_name=performops_result.app_deployment_name,
            summary=performops_result.summary_text,
            severity=performops_result.severity,
            influence=performops_result.analysis_result.resource.traffic.basis,
            cause=performops_result.analysis_result.result,
            actions=actions,
        )
