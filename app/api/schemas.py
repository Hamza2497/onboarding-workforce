import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.run import RunStatus


class RunCreate(BaseModel):
    repo_url: str


class RunCreateResponse(BaseModel):
    id: uuid.UUID


class BlackboardEntryRead(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    key: str
    scope: str
    value: Any
    source_refs: Any
    created_at: datetime

    model_config = {"from_attributes": True}


class RunRead(BaseModel):
    id: uuid.UUID
    repo_url: str
    status: RunStatus
    created_at: datetime
    finished_at: datetime | None
    blackboard_entries: list[BlackboardEntryRead]

    model_config = {"from_attributes": True}
