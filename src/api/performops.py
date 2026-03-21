from fastapi import APIRouter, Depends

from src.app.get_list import GetPerformopsListUseCase
from src.common.schema import CursorRequest
from src.deps.get_performops_core import get_performops_core
from src.core.performops.core import PerformOpsCore

performops_router = APIRouter(prefix='/performops', tags=['performops'])

# performops 목록 조회(생성 순 정렬)
# 원인, 영향, 심각성 상태
@performops_router.get('/{project_id}')
async def get_performops(
        project_id: int,
        cursor_request: CursorRequest = Depends(),
        usecase: GetPerformopsListUseCase = Depends(GetPerformopsListUseCase),
):
    return await usecase(project_id=project_id, cursor_request=cursor_request)

# performops 가동
@performops_router.post('/{project_id}/{app_deployment_name}')
async def performops(
        project_id: int,
        app_deployment_name: str,
):
    ...