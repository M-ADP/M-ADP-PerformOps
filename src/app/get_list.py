from fastapi import Depends

from src.app.base_usecase import BaseUseCase
from src.common.schema import CursorPage, CursorRequest
from src.core.performops.model import Performops
from src.core.uow import UnitOfWork
from src.deps.get_uow import get_uow


class GetPerformopsListUseCase(BaseUseCase):

    def __init__(self, uow: UnitOfWork = Depends(get_uow)):
        self.uow = uow

    async def __call__(self, project_id: int, cursor_request: CursorRequest) -> CursorPage[Performops]:
        return await self.uow.performops.get_by_project_id(project_id, cursor_request)
