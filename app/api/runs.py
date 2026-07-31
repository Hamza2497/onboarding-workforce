import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import BlackboardEntryRead, RunCreate, RunCreateResponse, RunRead
from app.db.session import get_session
from app.models import BlackboardEntry, Run

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=RunCreateResponse, status_code=201)
async def create_run(
    payload: RunCreate, session: AsyncSession = Depends(get_session)
) -> RunCreateResponse:
    run = Run(repo_url=payload.repo_url)
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return RunCreateResponse(id=run.id)


@router.get("/{run_id}", response_model=RunRead)
async def get_run(
    run_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> RunRead:
    run = await session.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    result = await session.execute(
        select(BlackboardEntry).where(BlackboardEntry.run_id == run_id)
    )
    entries = result.scalars().all()

    return RunRead(
        id=run.id,
        repo_url=run.repo_url,
        status=run.status,
        created_at=run.created_at,
        finished_at=run.finished_at,
        blackboard_entries=[
            BlackboardEntryRead.model_validate(e) for e in entries
        ],
    )
