import pytest
from sqlalchemy.exc import IntegrityError

from app.api.runs import get_run
from app.db.queries import mark_task_completed, visible_entries
from app.models import BlackboardEntry, Run, Task, TaskKind, TaskStatus


async def _make_run_and_task(db_session, status: TaskStatus) -> tuple[Run, Task]:
    run = Run(repo_url="https://github.com/example/repo")
    db_session.add(run)
    await db_session.flush()

    task = Task(run_id=run.id, kind=TaskKind.SETUP, status=status)
    db_session.add(task)
    await db_session.flush()
    return run, task


async def test_entries_from_running_or_failed_tasks_are_invisible(db_session):
    running_run, running_task = await _make_run_and_task(db_session, TaskStatus.RUNNING)
    db_session.add(
        BlackboardEntry(
            run_id=running_run.id,
            task_id=running_task.id,
            key="dependencies",
            value={"note": "running"},
        )
    )

    failed_run, failed_task = await _make_run_and_task(db_session, TaskStatus.FAILED)
    db_session.add(
        BlackboardEntry(
            run_id=failed_run.id,
            task_id=failed_task.id,
            key="dependencies",
            value={"note": "failed"},
        )
    )
    await db_session.commit()

    assert await visible_entries(db_session, running_run.id) == []
    assert await visible_entries(db_session, failed_run.id) == []

    running_result = await get_run(running_run.id, db_session)
    assert running_result.blackboard_entries == []

    failed_result = await get_run(failed_run.id, db_session)
    assert failed_result.blackboard_entries == []


async def test_entry_becomes_visible_once_task_completes(db_session):
    run, task = await _make_run_and_task(db_session, TaskStatus.RUNNING)
    entry = BlackboardEntry(
        run_id=run.id,
        task_id=task.id,
        key="dependencies",
        value={"note": "in progress"},
    )
    db_session.add(entry)
    await db_session.commit()

    assert await visible_entries(db_session, run.id) == []

    await mark_task_completed(db_session, task.id)
    await db_session.commit()

    visible = await visible_entries(db_session, run.id)
    assert [e.id for e in visible] == [entry.id]

    result = await get_run(run.id, db_session)
    assert [e.id for e in result.blackboard_entries] == [entry.id]


async def test_two_completed_tasks_cannot_own_the_same_fact(db_session):
    run = Run(repo_url="https://github.com/example/repo")
    db_session.add(run)
    await db_session.flush()

    first_task = Task(run_id=run.id, kind=TaskKind.DEPENDENCY)
    second_task = Task(run_id=run.id, kind=TaskKind.DEPENDENCY)
    db_session.add_all([first_task, second_task])
    await db_session.flush()

    db_session.add(
        BlackboardEntry(
            run_id=run.id,
            task_id=first_task.id,
            key="dependencies",
            scope="pkg-a",
            value={"attempt": 1},
        )
    )
    await mark_task_completed(db_session, first_task.id)
    await db_session.commit()

    db_session.add(
        BlackboardEntry(
            run_id=run.id,
            task_id=second_task.id,
            key="dependencies",
            scope="pkg-a",
            value={"attempt": 2},
        )
    )
    await db_session.flush()

    with pytest.raises(IntegrityError):
        await mark_task_completed(db_session, second_task.id)
    await db_session.rollback()


async def test_failed_attempt_then_successful_retry_succeeds(db_session):
    run = Run(repo_url="https://github.com/example/repo")
    db_session.add(run)
    await db_session.flush()

    failed_task = Task(run_id=run.id, kind=TaskKind.DEPENDENCY, status=TaskStatus.FAILED)
    db_session.add(failed_task)
    await db_session.flush()

    db_session.add(
        BlackboardEntry(
            run_id=run.id,
            task_id=failed_task.id,
            key="dependencies",
            scope="pkg-a",
            value={"attempt": 1},
        )
    )
    await db_session.commit()

    retry_task = Task(run_id=run.id, kind=TaskKind.DEPENDENCY, status=TaskStatus.RUNNING)
    db_session.add(retry_task)
    await db_session.flush()

    retry_entry = BlackboardEntry(
        run_id=run.id,
        task_id=retry_task.id,
        key="dependencies",
        scope="pkg-a",
        value={"attempt": 2},
    )
    db_session.add(retry_entry)
    await mark_task_completed(db_session, retry_task.id)
    await db_session.commit()

    visible = await visible_entries(db_session, run.id, key="dependencies", scope="pkg-a")
    assert [e.id for e in visible] == [retry_entry.id]
