from fastapi import Depends
from src.app.base_usecase import BaseUseCase
from src.core.performops.core import PerformOpsCore
from src.core.performops.model import PerformOpsResult
from src.core.uow import UnitOfWork
from src.deps.get_performops_core import get_performops_core
from src.deps.get_uow import get_uow


class StartPerformopsListUseCase(BaseUseCase):
    def __init__(
        self,
        uow: UnitOfWork = Depends(get_uow),
        performops_core: PerformOpsCore = Depends(get_performops_core),
    ):
        self.uow = uow
        self.performops_core = performops_core

    async def __call__(
        self, project_id: int, app_deployment_name: str
    ) -> PerformOpsResult:
        performops_result = await self.performops_core.start(
            project_id=project_id, app_deployment_name=app_deployment_name
        )

        await self.uow.performops.save(performops_result)

        return performops_result
