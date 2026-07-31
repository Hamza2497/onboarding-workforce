from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BlackboardEntry


@dataclass
class AgentContext:
    run_id: UUID
    task_id: UUID
    session: AsyncSession


class Agent(ABC):
    """`reads` and `produces` declare the board keys this agent depends on and
    writes, so a planner can derive dependency edges instead of them being
    hand-authored.
    """

    reads: ClassVar[frozenset[str]] = frozenset()
    produces: ClassVar[frozenset[str]] = frozenset()

    @abstractmethod
    async def run(self, ctx: AgentContext) -> list[BlackboardEntry]:
        raise NotImplementedError
