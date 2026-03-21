from fastapi import APIRouter, Depends

from src.app.get_list import GetPerformopsListUseCase
from src.app.start_performops import StartPerformopsListUseCase
from src.common.schema import CursorPage, CursorRequest
from src.core.performops.model import PerformOpsResult

performops_router = APIRouter(prefix='/performops', tags=['performops'])


@performops_router.get('/{project_id}', response_model=CursorPage)
async def get_performops(
        project_id: int,
        cursor_request: CursorRequest = Depends(),
        usecase: GetPerformopsListUseCase = Depends(GetPerformopsListUseCase),
):
    return await usecase(project_id=project_id, cursor_request=cursor_request)


@performops_router.post('/{project_id}/{app_deployment_name}', response_model=PerformOpsResult)
async def start_performops(
        project_id: int,
        app_deployment_name: str,
        usecase: StartPerformopsListUseCase = Depends(StartPerformopsListUseCase),
):
    return await usecase(project_id=project_id, app_deployment_name=app_deployment_name)
