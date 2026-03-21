from abc import ABC, abstractmethod

from src.core.performops.repository import PerformopsRepository


class UnitOfWork(ABC):

    performops: PerformopsRepository

    @abstractmethod
    async def __aenter__(self):
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError

    @abstractmethod
    async def commit(self):
        raise NotImplementedError

    @abstractmethod
    async def rollback(self):
        raise NotImplementedError
