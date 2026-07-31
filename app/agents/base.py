from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BlackboardEntry


@dataclass
class AgentContext:
    run_id: UUID
    task_id: UUID
    session: AsyncSession


class Agent(ABC):
    @abstractmethod
    async def run(self, ctx: AgentContext) -> list[BlackboardEntry]:
        raise NotImplementedError
