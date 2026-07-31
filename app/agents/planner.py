from collections.abc import Sequence

from app.agents.base import Agent


class PlanValidationError(Exception):
    """Raised at plan time, before any task rows exist, when a set of agents
    cannot be assembled into a valid dependency graph."""


def validate_agent_graph(
    agent_classes: Sequence[type[Agent]],
) -> dict[type[Agent], frozenset[type[Agent]]]:
    """Derives dependency edges from declared reads/produces and validates
    the resulting graph. Returns, for each agent class, the set of agent
    classes it depends on (i.e. that produce a key it reads).

    Raises PlanValidationError on:
      - two agents declaring the same produced key
      - a needed key that no agent produces
      - a cycle in the resulting graph
    """
    produced_by: dict[str, type[Agent]] = {}
    for cls in agent_classes:
        for key in cls.produces:
            existing = produced_by.get(key)
            if existing is not None:
                raise PlanValidationError(
                    f"key {key!r} is produced by both "
                    f"{existing.__name__} and {cls.__name__}"
                )
            produced_by[key] = cls

    for cls in agent_classes:
        missing = cls.reads - produced_by.keys()
        if missing:
            raise PlanValidationError(
                f"{cls.__name__} needs key(s) {sorted(missing)} that no agent produces"
            )

    edges: dict[type[Agent], frozenset[type[Agent]]] = {
        cls: frozenset(produced_by[key] for key in cls.reads) for cls in agent_classes
    }

    _assert_acyclic(edges)
    return edges


def _assert_acyclic(edges: dict[type[Agent], frozenset[type[Agent]]]) -> None:
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[type[Agent], int] = dict.fromkeys(edges, WHITE)

    def visit(node: type[Agent], path: list[type[Agent]]) -> None:
        color[node] = GRAY
        path.append(node)
        for dep in edges[node]:
            if color[dep] == GRAY:
                cycle = path[path.index(dep):] + [dep]
                names = " -> ".join(c.__name__ for c in cycle)
                raise PlanValidationError(f"cycle in agent dependency graph: {names}")
            if color[dep] == WHITE:
                visit(dep, path)
        path.pop()
        color[node] = BLACK

    for node in edges:
        if color[node] == WHITE:
            visit(node, [])
