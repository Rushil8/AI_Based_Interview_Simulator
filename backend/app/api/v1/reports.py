import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.session import InterviewSession
from app.models.report import SessionReport
from app.schemas.report import SessionReportResponse, DimensionScores, FeedbackReport, QuestionReviewItem
from app.services.report_service import report_service

router = APIRouter(tags=["Reports"])


@router.get("/interviews/{session_id}/report", response_model=SessionReportResponse)
def get_session_report(session_id: str, db: Session = Depends(get_db)):
    """
    Returns the comprehensive persisted session report, charts data, and feedback.
    Generates report on-the-fly if session is completed but report hasn't been compiled yet.
    """
    report_record = db.query(SessionReport).filter(SessionReport.session_id == session_id).first()
    if not report_record:
        # Check if session exists and is completed
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found.")
        try:
            return report_service.generate_and_save_session_report(db, session_id)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate report: {str(e)}")

    # Deserialize stored report payload
    session = report_record.session
    report_data = json.loads(report_record.report_json) if report_record.report_json else {}
    feedback_data = json.loads(report_record.feedback_json) if report_record.feedback_json else {}
    dim_data = report_data.get("dimension_scores", {})
    comp_scores = json.loads(report_record.competency_scores_json) if report_record.competency_scores_json else []

    question_reviews = [
        QuestionReviewItem(**qr) for qr in report_data.get("question_reviews", [])
    ]

    return SessionReportResponse(
        id=report_record.id,
        session_id=session_id,
        job_role=session.job_role if session else "Target Role",
        overall_score=report_record.overall_score,
        performance_summary=report_data.get("performance_summary", "Session performance summary"),
        dimension_scores=DimensionScores(
            relevance=dim_data.get("relevance", report_record.relevance_avg),
            technical_correctness=dim_data.get("technical", report_record.technical_avg),
            completeness=dim_data.get("completeness", report_record.completeness_avg),
            communication=dim_data.get("communication", report_record.communication_avg),
        ),
        competency_scores=comp_scores,
        strongest_competencies=report_data.get("strongest_competencies", []),
        weakest_competencies=report_data.get("weakest_competencies", []),
        answered_count=report_data.get("answered_count", 0),
        skipped_count=report_data.get("skipped_count", 0),
        coverage_pct=report_data.get("coverage_pct", 0.0),
        difficulty_distribution=report_data.get("difficulty_distribution", {}),
        question_reviews=question_reviews,
        feedback=FeedbackReport(**feedback_data),
        generated_at=report_record.generated_at,
    )
