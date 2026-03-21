from typing import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.uow import UnitOfWork
from src.infra.db.session import AsyncSessionFactory
from src.infra.db.uow import SqlAlchemyUnitOfWork


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionFactory() as session:
        yield session


async def get_uow(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncIterator[UnitOfWork]:
    uow = SqlAlchemyUnitOfWork(session)
    try:
        yield uow
    finally:
        await uow.session.close()
