from sqlalchemy.ext.asyncio import AsyncSession

from src.core.uow import UnitOfWork
from src.core.performops.repository import PerformopsRepository
from src.infra.db.performops.repository import PerformopsRepositoryImpl


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.performops: PerformopsRepository = PerformopsRepositoryImpl(session)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
        else:
            await self.commit()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
