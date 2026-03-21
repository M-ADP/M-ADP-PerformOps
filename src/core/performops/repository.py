from abc import ABC, abstractmethod
from typing import List

from src.common.schema import CursorPage, CursorRequest
from src.core.performops.model import Performops


class PerformopsRepository(ABC):

    @abstractmethod
    async def get_by_project_id(self, project_id: int, cursor_request: CursorRequest) -> CursorPage[Performops]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, performops: Performops) -> Performops:
        raise NotImplementedError
