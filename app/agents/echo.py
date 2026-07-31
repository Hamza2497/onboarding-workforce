from app.agents.base import Agent, AgentContext
from app.models import BlackboardEntry


class EchoAgent(Agent):
    reads: frozenset[str] = frozenset()
    produces: frozenset[str] = frozenset({"echo"})

    async def run(self, ctx: AgentContext) -> list[BlackboardEntry]:
        entry = BlackboardEntry(
            run_id=ctx.run_id,
            task_id=ctx.task_id,
            key="echo",
            value={"message": "echo"},
            source_refs={},
        )
        return [entry]
