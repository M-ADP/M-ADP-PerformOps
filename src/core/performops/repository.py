from abc import ABC, abstractmethod
from typing import List

from src.common.schema import CursorPage, CursorRequest
from src.core.performops.model import (
    ActionState,
    Performops,
    PerformOpsAction,
    PerformOpsResult,
)


class PerformopsRepository(ABC):
    @abstractmethod
    async def get_by_project_id(
        self, project_id: int, cursor_request: CursorRequest
    ) -> CursorPage[Performops]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, performops_result: PerformOpsResult) -> Performops:
        raise NotImplementedError

    @abstractmethod
    async def get_actions_by_ids(self, action_ids: List[int]) -> List[PerformOpsAction]:
        """action_ids 순서를 유지하여 반환"""
        raise NotImplementedError

    @abstractmethod
    async def update_action_state(self, action_id: int, state: ActionState) -> None:
        raise NotImplementedError
