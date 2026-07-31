import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.session import get_session
from app.main import app

test_engine = create_async_engine(settings.database_url, future=True, poolclass=NullPool)
test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)


async def _get_test_session():
    async with test_session_factory() as session:
        yield session


app.dependency_overrides[get_session] = _get_test_session


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _dispose_engine_at_session_end():
    yield
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session():
    async with test_session_factory() as session:
        yield session
        await session.rollback()

    async with test_engine.begin() as conn:
        await conn.execute(text("DELETE FROM blackboard_entries"))
        await conn.execute(text("DELETE FROM tasks"))
        await conn.execute(text("DELETE FROM runs"))
