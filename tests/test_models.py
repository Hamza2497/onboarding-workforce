from sqlalchemy import select

from app.models import BlackboardEntry, Run, RunStatus, Task, TaskKind, TaskStatus


async def test_run_round_trip(db_session):
    run = Run(repo_url="https://github.com/example/repo")
    db_session.add(run)
    await db_session.commit()

    fetched = await db_session.get(Run, run.id)
    assert fetched is not None
    assert fetched.repo_url == "https://github.com/example/repo"
    assert fetched.status == RunStatus.PENDING
    assert fetched.created_at is not None
    assert fetched.finished_at is None


async def test_task_round_trip(db_session):
    run = Run(repo_url="https://github.com/example/repo")
    db_session.add(run)
    await db_session.flush()

    upstream = Task(run_id=run.id, kind=TaskKind.SETUP, status=TaskStatus.COMPLETED)
    db_session.add(upstream)
    await db_session.flush()

    task = Task(
        run_id=run.id,
        kind=TaskKind.ARCHITECTURE_MAPPER,
        depends_on=[upstream.id],
        attempt_count=1,
    )
    db_session.add(task)
    await db_session.commit()

    fetched = await db_session.get(Task, task.id)
    assert fetched is not None
    assert fetched.run_id == run.id
    assert fetched.kind == TaskKind.ARCHITECTURE_MAPPER
    assert fetched.status == TaskStatus.PENDING
    assert fetched.depends_on == [upstream.id]
    assert fetched.attempt_count == 1
    assert fetched.error is None


async def test_blackboard_entry_round_trip(db_session):
    run = Run(repo_url="https://github.com/example/repo")
    db_session.add(run)
    await db_session.flush()

    task = Task(run_id=run.id, kind=TaskKind.CONVENTIONS)
    db_session.add(task)
    await db_session.flush()

    entry = BlackboardEntry(
        run_id=run.id,
        task_id=task.id,
        key="conventions.linting",
        value={"tool": "ruff"},
        source_refs={"file": "pyproject.toml", "lines": [1, 10]},
    )
    db_session.add(entry)
    await db_session.commit()

    result = await db_session.execute(
        select(BlackboardEntry).where(BlackboardEntry.id == entry.id)
    )
    fetched = result.scalar_one()
    assert fetched.run_id == run.id
    assert fetched.task_id == task.id
    assert fetched.key == "conventions.linting"
    assert fetched.value == {"tool": "ruff"}
    assert fetched.source_refs == {"file": "pyproject.toml", "lines": [1, 10]}
    assert fetched.created_at is not None
