from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.common.config import settings

engine = create_async_engine(settings.database_url)

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)
