from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.schema import CursorPage, CursorRequest
from src.core.performops.model import Performops, PerformOpsResult
from src.core.performops.repository import PerformopsRepository
from src.infra.db.performops.model import PerformOps


class PerformopsRepositoryImpl(PerformopsRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_project_id(self, project_id: int, cursor_request: CursorRequest) -> CursorPage[Performops]:
        query = select(PerformOps).where(PerformOps.project_id == project_id)

        if cursor_request.cursor is not None:
            query = query.where(PerformOps.id > cursor_request.cursor)

        query = query.order_by(PerformOps.id).limit(cursor_request.size + 1)

        result = await self.session.execute(query)
        rows = result.scalars().all()

        has_next = len(rows) > cursor_request.size
        items = [self._to_domain(row) for row in rows[:cursor_request.size]]

        return CursorPage(items=items, has_next=has_next)

    async def save(self, performops_result: PerformOpsResult) -> Performops:
        model = self._to_model(performops_result)
        self.session.add(model)
        await self.session.flush()
        return self._to_domain(model)

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
        )

    def _to_model(self, performops_result: PerformOpsResult) -> PerformOps:
        return PerformOps(
            project_id=performops_result.project_id,
            app_deployment_name=performops_result.app_deployment_name,
            summary=performops_result.summary_text,
            severity=performops_result.severity,
            influence=performops_result.analysis_result,
            cause=performops_result.analysis_result,
        )
