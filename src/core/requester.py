from abc import ABC, abstractmethod
from typing import Any, Optional


class Requester(ABC):
    @abstractmethod
    async def get(self, url: str, **kwargs) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def post(self, url: str, body: Any = None, **kwargs) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def patch(self, url: str, body: Any = None, **kwargs) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def put(self, url: str, body: Any = None, **kwargs) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, url: str, **kwargs) -> Any:
        raise NotImplementedError
