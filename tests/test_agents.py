from app.agents import Agent, AgentContext, EchoAgent
from app.models import BlackboardEntry, Run, Task, TaskKind


async def test_echo_agent_satisfies_agent_interface(db_session):
    agent = EchoAgent()
    assert isinstance(agent, Agent)

    run = Run(repo_url="https://github.com/example/repo")
    db_session.add(run)
    await db_session.flush()

    task = Task(run_id=run.id, kind=TaskKind.SETUP)
    db_session.add(task)
    await db_session.flush()

    ctx = AgentContext(run_id=run.id, task_id=task.id, session=db_session)
    entries = await agent.run(ctx)

    assert isinstance(entries, list)
    assert len(entries) == 1
    assert all(isinstance(e, BlackboardEntry) for e in entries)
    assert entries[0].run_id == run.id
    assert entries[0].task_id == task.id
