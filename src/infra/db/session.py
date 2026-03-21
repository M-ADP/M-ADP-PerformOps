from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.common.config.database import DatabaseConfig

engine = create_async_engine(DatabaseConfig.URL)

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)
