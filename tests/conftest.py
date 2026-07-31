import pytest_asyncio
from sqlalchemy import text

from app.db.session import async_session_factory, engine


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _dispose_engine_at_session_end():
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session():
    async with async_session_factory() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM blackboard_entries"))
        await conn.execute(text("DELETE FROM tasks"))
        await conn.execute(text("DELETE FROM runs"))
