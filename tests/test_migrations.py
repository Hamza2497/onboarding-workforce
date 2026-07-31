import importlib.util
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import inspect, text

from tests.conftest import test_engine


def _run_alembic(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        capture_output=True,
        text=True,
    )


def test_alembic_upgrade_head_applies_cleanly():
    result = _run_alembic("upgrade", "head")
    assert result.returncode == 0, result.stderr


async def test_expected_tables_exist():
    async with test_engine.connect() as conn:
        table_names = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())

    assert {"runs", "tasks", "blackboard_entries"}.issubset(set(table_names))


def _load_migration_module():
    versions_dir = Path(__file__).resolve().parent.parent / "alembic" / "versions"
    path = next(versions_dir.glob("faa230ff6b03_*.py"))
    spec = importlib.util.spec_from_file_location("faa230ff6b03_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
async def pre_migration_state():
    """Rewind the DB to just before faa230ff6b03, restore head afterward."""
    migration = _load_migration_module()
    down_revision = migration.down_revision

    result = _run_alembic("downgrade", down_revision)
    assert result.returncode == 0, result.stderr

    yield

    result = _run_alembic("upgrade", "head")
    assert result.returncode == 0, result.stderr


async def test_scope_and_visibility_backfill_on_populated_table(pre_migration_state):
    run_id = uuid.uuid4()
    completed_task_id = uuid.uuid4()
    failed_task_id = uuid.uuid4()
    completed_entry_id = uuid.uuid4()
    failed_entry_id = uuid.uuid4()

    async with test_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO runs (id, repo_url, status) "
                "VALUES (:id, 'https://example.com/repo', 'RUNNING')"
            ),
            {"id": run_id},
        )
        await conn.execute(
            text(
                "INSERT INTO tasks (id, run_id, kind, status, depends_on, attempt_count) "
                "VALUES (:id, :run_id, 'SETUP', :status, '{}', 0)"
            ),
            [
                {"id": completed_task_id, "run_id": run_id, "status": "COMPLETED"},
                {"id": failed_task_id, "run_id": run_id, "status": "FAILED"},
            ],
        )
        await conn.execute(
            text(
                "INSERT INTO blackboard_entries (id, run_id, task_id, key, value, source_refs) "
                "VALUES (:id, :run_id, :task_id, :key, '{}', '{}')"
            ),
            [
                {
                    "id": completed_entry_id,
                    "run_id": run_id,
                    "task_id": completed_task_id,
                    "key": "k1",
                },
                {
                    "id": failed_entry_id,
                    "run_id": run_id,
                    "task_id": failed_task_id,
                    "key": "k2",
                },
            ],
        )

    result = _run_alembic("upgrade", "head")
    assert result.returncode == 0, result.stderr

    async with test_engine.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    "SELECT id, scope, is_visible FROM blackboard_entries "
                    "WHERE id IN (:completed_id, :failed_id)"
                ),
                {"completed_id": completed_entry_id, "failed_id": failed_entry_id},
            )
        ).mappings().all()

    by_id = {row["id"]: row for row in rows}
    assert by_id[completed_entry_id]["scope"] is not None
    assert by_id[completed_entry_id]["is_visible"] is True
    assert by_id[failed_entry_id]["scope"] is not None
    assert by_id[failed_entry_id]["is_visible"] is False

    async with test_engine.begin() as conn:
        await conn.execute(text("DELETE FROM blackboard_entries"))
        await conn.execute(text("DELETE FROM tasks"))
        await conn.execute(text("DELETE FROM runs"))
