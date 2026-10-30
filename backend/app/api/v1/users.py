from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.session import InterviewSession
from app.models.report import SessionReport
from app.config import settings

router = APIRouter(tags=["Users & History"])


class SessionHistoryItem(BaseModel):
    id: str
    job_role: str
    difficulty: str
    status: str
    target_question_count: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    overall_score: Optional[float] = None
    has_report: bool


class SystemConfigResponse(BaseModel):
    app_name: str
    app_version: str
    environment: str
    gemini_model: str
    mock_ai: bool
    rubric_version: str
    weights: dict
    semantic_flag_threshold: float


@router.get("/users/me/interviews", response_model=List[SessionHistoryItem])
def get_user_interviews(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Returns candidate interview history with scores, target roles, and dates for history page.
    """
    sessions = (
        db.query(InterviewSession)
        .order_by(InterviewSession.started_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    history = []
    for s in sessions:
        report = db.query(SessionReport).filter(SessionReport.session_id == s.id).first()
        history.append(SessionHistoryItem(
            id=s.id,
            job_role=s.job_role,
            difficulty=s.difficulty,
            status=s.status,
            target_question_count=s.target_question_count,
            started_at=s.started_at,
            completed_at=s.completed_at,
            overall_score=report.overall_score if report else None,
            has_report=report is not None,
        ))

    return history


@router.get("/config", response_model=SystemConfigResponse)
def get_system_config():
    """
    Returns transparent system settings, rubric weights, and AI configuration.
    """
    return SystemConfigResponse(
        app_name=settings.APP_NAME,
        app_version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        gemini_model=settings.GEMINI_MODEL,
        mock_ai=settings.MOCK_AI,
        rubric_version=settings.RUBRIC_VERSION,
        weights={
            "relevance": settings.RUBRIC_WEIGHT_RELEVANCE,
            "technical_correctness": settings.RUBRIC_WEIGHT_TECHNICAL,
            "completeness": settings.RUBRIC_WEIGHT_COMPLETENESS,
            "communication": settings.RUBRIC_WEIGHT_COMMUNICATION,
        },
        semantic_flag_threshold=settings.SEMANTIC_SIMILARITY_FLAG_THRESHOLD,
    )
