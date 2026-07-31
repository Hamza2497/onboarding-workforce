import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BlackboardEntry, Task, TaskStatus


async def visible_entries(
    session: AsyncSession,
    run_id: uuid.UUID,
    *,
    key: str | None = None,
    scope: str | None = None,
) -> list[BlackboardEntry]:
    """The single read path for board facts: only rows whose owning task
    completed successfully are visible. Every board read must go through
    this, including get_run.
    """
    stmt = select(BlackboardEntry).where(
        BlackboardEntry.run_id == run_id,
        BlackboardEntry.is_visible.is_(True),
    )
    if key is not None:
        stmt = stmt.where(BlackboardEntry.key == key)
    if scope is not None:
        stmt = stmt.where(BlackboardEntry.scope == scope)

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def mark_task_completed(session: AsyncSession, task_id: uuid.UUID) -> None:
    """Flips a task to COMPLETED and makes its blackboard entries visible in
    the same transaction. This is the only path that should ever set
    is_visible=True, which is what the partial unique index relies on to
    enforce one-owner-per-fact among completed attempts.
    """
    await session.execute(
        update(Task).where(Task.id == task_id).values(status=TaskStatus.COMPLETED)
    )
    await session.execute(
        update(BlackboardEntry)
        .where(BlackboardEntry.task_id == task_id)
        .values(is_visible=True)
    )
