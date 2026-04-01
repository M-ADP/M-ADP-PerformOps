#!/usr/bin/env python3
"""Initialize the database schema for performops service."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine
from src.common.config.database import DatabaseConfig
from src.infra.db.base_entity import Base

# Import models to register them with Base
from src.infra.db.performops.model import PerformOps, PerformOpsAction


async def init_db():
    """Create all tables in the database."""
    print(f"Connecting to database: {DatabaseConfig.URL}")

    engine = create_async_engine(DatabaseConfig.URL, echo=True)

    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully!")

    await engine.dispose()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(init_db())
