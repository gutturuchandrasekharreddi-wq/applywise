"""ApplyWise FastAPI application."""

import sqlite3
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import get_db
from .matching import compare_text
from .models import create, delete, list_all, overview as get_overview, update
from .schemas import ApplicationCreate, ApplicationRead, ApplicationUpdate, MatchRequest, MatchResult

app = FastAPI(
    title="ApplyWise API",
    description="A local-first job search tracker with explainable resume matching.",
    version="1.0.0",
)
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/overview")
def overview(db: sqlite3.Connection = Depends(get_db)) -> dict[str, object]:
    return get_overview(db)


@app.get("/api/applications", response_model=list[ApplicationRead])
def list_applications(
    status_filter: str | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None, max_length=120),
    db: sqlite3.Connection = Depends(get_db),
) -> list[ApplicationRead]:
    return [ApplicationRead.model_validate(item) for item in list_all(db, status_filter, q)]


@app.post("/api/applications", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate, db: sqlite3.Connection = Depends(get_db)
) -> ApplicationRead:
    item = create(db, payload.model_dump(mode="json"))
    return ApplicationRead.model_validate(item)


@app.patch("/api/applications/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    db: sqlite3.Connection = Depends(get_db),
) -> ApplicationRead:
    item = update(db, application_id, payload.model_dump(exclude_unset=True, mode="json"))
    if item is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return ApplicationRead.model_validate(item)


@app.delete("/api/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(application_id: int, db: sqlite3.Connection = Depends(get_db)) -> Response:
    if not delete(db, application_id):
        raise HTTPException(status_code=404, detail="Application not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/api/match", response_model=MatchResult)
def match_resume(payload: MatchRequest) -> dict[str, object]:
    return compare_text(payload.resume_text, payload.job_description)
