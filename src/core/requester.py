from abc import ABC, abstractmethod
from typing import Any


class Requester(ABC):

    @abstractmethod
    async def post(self, url: str, body: Any = None, **kwargs) -> Any:
        raise NotImplementedError
