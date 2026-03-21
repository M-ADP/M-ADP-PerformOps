from abc import ABC, abstractmethod

from src.core.performops.model import Performops


class PerformopsRepository(ABC):

    @abstractmethod
    async def get_by_project_id(self, project_id: int) -> list[Performops]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, performops: Performops) -> Performops:
        raise NotImplementedError
