"""ApplyWise FastAPI application."""

from datetime import date
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .matching import compare_text
from .models import Application
from .schemas import ApplicationCreate, ApplicationRead, ApplicationUpdate, MatchRequest, MatchResult

Base.metadata.create_all(bind=engine)

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
def overview(db: Session = Depends(get_db)) -> dict[str, object]:
    total = db.scalar(select(func.count()).select_from(Application)) or 0
    grouped = dict(db.execute(select(Application.status, func.count()).group_by(Application.status)).all())
    applied = grouped.get("applied", 0) + grouped.get("interview", 0) + grouped.get("offer", 0) + grouped.get("rejected", 0)
    responses = grouped.get("interview", 0) + grouped.get("offer", 0) + grouped.get("rejected", 0)
    follow_up_count = db.scalar(
        select(func.count()).select_from(Application).where(
            Application.follow_up_on.is_not(None),
            Application.follow_up_on <= date.today(),
            Application.status.not_in(["offer", "rejected", "withdrawn"]),
        )
    ) or 0
    follow_ups = db.scalars(
        select(Application)
        .where(Application.follow_up_on.is_not(None), Application.follow_up_on <= date.today(), Application.status.not_in(["offer", "rejected", "withdrawn"]))
        .order_by(Application.follow_up_on)
        .limit(5)
    ).all()
    recent = db.scalars(select(Application).order_by(Application.updated_at.desc()).limit(5)).all()
    return {
        "total": total,
        "by_status": grouped,
        "response_rate": round(responses / applied * 100) if applied else 0,
        "follow_up_count": follow_up_count,
        "follow_ups": [ApplicationRead.model_validate(item) for item in follow_ups],
        "recent": [ApplicationRead.model_validate(item) for item in recent],
    }


@app.get("/api/applications", response_model=list[ApplicationRead])
def list_applications(
    status_filter: str | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None, max_length=120),
    db: Session = Depends(get_db),
) -> list[Application]:
    query = select(Application)
    if status_filter:
        query = query.where(Application.status == status_filter)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.where(or_(Application.company.ilike(pattern), Application.role.ilike(pattern), Application.location.ilike(pattern)))
    return list(db.scalars(query.order_by(Application.updated_at.desc())).all())


@app.post("/api/applications", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)) -> Application:
    item = Application(**payload.model_dump(mode="json"))
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.patch("/api/applications/{application_id}", response_model=ApplicationRead)
def update_application(application_id: int, payload: ApplicationUpdate, db: Session = Depends(get_db)) -> Application:
    item = db.get(Application, application_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Application not found")
    for field, value in payload.model_dump(exclude_unset=True, mode="json").items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@app.delete("/api/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(application_id: int, db: Session = Depends(get_db)) -> Response:
    item = db.get(Application, application_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/api/match", response_model=MatchResult)
def match_resume(payload: MatchRequest) -> dict[str, object]:
    return compare_text(payload.resume_text, payload.job_description)
