from typing import List

from fastapi import APIRouter, Depends, Query

from src.app.approve_performops import ApprovePerformopsUseCase
from src.app.get_list import GetPerformopsListUseCase
from src.app.start_performops import StartPerformopsListUseCase
from src.common.schema import CursorPage, CursorRequest, SuccessResponse
from src.core.performops.model import Performops, PerformOpsResult

performops_router = APIRouter(prefix="/performops", tags=["performops"])


@performops_router.get(
    "/{project_id}",
    response_model=SuccessResponse[CursorPage[Performops]],
)
async def get_performops(
    project_id: int,
    cursor_request: CursorRequest = Depends(),
    usecase: GetPerformopsListUseCase = Depends(GetPerformopsListUseCase),
):
    data = await usecase(project_id=project_id, cursor_request=cursor_request)
    return SuccessResponse(message="ok", data=data)


@performops_router.post(
    "/{project_id}/{app_deployment_name}",
    response_model=SuccessResponse[PerformOpsResult],
)
async def start_performops(
    project_id: int,
    app_deployment_name: str,
    usecase: StartPerformopsListUseCase = Depends(StartPerformopsListUseCase),
):
    data = await usecase(project_id=project_id, app_deployment_name=app_deployment_name)
    return SuccessResponse(message="ok", data=data)


@performops_router.post(
    "/{performops_id}/approve",
    response_model=SuccessResponse[Performops],
)
async def approve_performops(
    performops_id: int,
    action_ids: List[int] = Query(
        ..., description="실행할 action id 목록 (계획 순서대로)"
    ),
    usecase: ApprovePerformopsUseCase = Depends(ApprovePerformopsUseCase),
):
    data = await usecase(performops_id=performops_id, action_ids=action_ids)
    return SuccessResponse(message="ok", data=data)
