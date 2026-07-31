from fastapi import FastAPI

from app.api.runs import router as runs_router

app = FastAPI(title="onboarding-workforce")

app.include_router(runs_router)
