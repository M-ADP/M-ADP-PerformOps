from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.performops.model import Performops
from src.core.performops.repository import PerformopsRepository
from src.infra.db.performops.model import PerformOps


class PerformopsRepositoryImpl(PerformopsRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_project_id(self, project_id: int) -> list[Performops]:
        result = await self.session.execute(
            select(PerformOps).where(PerformOps.project_id == project_id)
        )
        return [self._to_domain(row) for row in result.scalars().all()]

    async def save(self, performops: Performops) -> Performops:
        model = self._to_model(performops)
        self.session.add(model)
        await self.session.flush()
        return self._to_domain(model)

    def _to_domain(self, model: PerformOps) -> Performops:
        return Performops(
            id=model.id,
            project_id=model.project_id,
            deployment_id=model.deployment_id,
            summary=model.summary,
            influence=model.influence,
            cause=model.cause,
            severity=model.severity,
            created_at=model.created_at,
        )

    def _to_model(self, performops: Performops) -> PerformOps:
        return PerformOps(
            project_id=performops.project_id,
            deployment_id=performops.deployment_id,
            summary=performops.summary,
            influence=performops.influence,
            cause=performops.cause,
            severity=performops.severity,
        )
