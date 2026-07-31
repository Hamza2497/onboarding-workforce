import pytest

from app.agents.base import Agent, AgentContext
from app.agents.planner import PlanValidationError, validate_agent_graph
from app.models import BlackboardEntry


class _StubAgent(Agent):
    async def run(self, ctx: AgentContext) -> list[BlackboardEntry]:
        return []


def _agent(name: str, reads: frozenset[str], produces: frozenset[str]) -> type[Agent]:
    return type(name, (_StubAgent,), {"reads": reads, "produces": produces})


def test_valid_graph_derives_edges():
    setup = _agent("SetupAgent", frozenset(), frozenset({"setup.summary"}))
    deps = _agent(
        "DependencyAgent", frozenset({"setup.summary"}), frozenset({"dependencies"})
    )
    composition = _agent(
        "CompositionAgent", frozenset({"setup.summary", "dependencies"}), frozenset({"guide"})
    )

    edges = validate_agent_graph([setup, deps, composition])

    assert edges[setup] == frozenset()
    assert edges[deps] == frozenset({setup})
    assert edges[composition] == frozenset({setup, deps})


def test_duplicate_produced_key_raises():
    first = _agent("First", frozenset(), frozenset({"dependencies"}))
    second = _agent("Second", frozenset(), frozenset({"dependencies"}))

    with pytest.raises(PlanValidationError, match="produced by both"):
        validate_agent_graph([first, second])


def test_missing_producer_raises():
    consumer = _agent("Consumer", frozenset({"nonexistent"}), frozenset())

    with pytest.raises(PlanValidationError, match="no agent produces"):
        validate_agent_graph([consumer])


def test_cycle_raises():
    a = _agent("A", frozenset({"b.out"}), frozenset({"a.out"}))
    b = _agent("B", frozenset({"a.out"}), frozenset({"b.out"}))

    with pytest.raises(PlanValidationError, match="cycle"):
        validate_agent_graph([a, b])
