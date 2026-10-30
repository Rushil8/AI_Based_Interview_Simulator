import json
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.session import InterviewSession
from app.models.report import SessionReport
from app.models.evaluation import AnswerEvaluation
from app.models.question import InterviewQuestion
from app.services.scoring_service import scoring_service
from app.services.feedback_service import feedback_service
from app.schemas.report import SessionReportResponse, DimensionScores, FeedbackReport, QuestionReviewItem


class ReportService:
    @staticmethod
    def generate_and_save_session_report(
        db: Session,
        session_id: str
    ) -> SessionReportResponse:
        """
        Builds the complete final interview report, generates feedback, persists to SessionReport,
        and marks InterviewSession as 'completed'.
        """
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if not session:
            raise ValueError(f"Session with id '{session_id}' not found.")

        competencies = session.competencies
        questions = db.query(InterviewQuestion).filter(InterviewQuestion.session_id == session_id).order_by(InterviewQuestion.sequence_number.asc()).all()

        # Build evaluation lookup
        evaluations_by_q_id: Dict[str, AnswerEvaluation] = {}
        question_eval_summaries = []
        difficulty_distribution: Dict[str, int] = {}
        question_reviews: List[QuestionReviewItem] = []

        for q in questions:
            difficulty_distribution[q.difficulty] = difficulty_distribution.get(q.difficulty, 0) + 1

            # Fetch answer and evaluation if exists
            ans = q.answers[0] if q.answers else None
            ev = ans.evaluation if (ans and ans.evaluation) else None

            if ev:
                evaluations_by_q_id[q.id] = ev
                evidence_dict = json.loads(ev.evidence_json) if ev.evidence_json else {}
                correct_c = json.loads(ev.correct_concepts_json) if ev.correct_concepts_json else []
                missing_c = json.loads(ev.missing_concepts_json) if ev.missing_concepts_json else []
                incorrect_c = json.loads(ev.incorrect_claims_json) if ev.incorrect_claims_json else []
                suggested_i = json.loads(ev.suggested_improvements_json) if ev.suggested_improvements_json else []

                question_eval_summaries.append({
                    "sequence_number": q.sequence_number,
                    "competency_name": q.competency.name if q.competency else "Core",
                    "question_text": q.question_text,
                    "weighted_score": ev.weighted_score,
                    "correct_concepts": correct_c,
                    "missing_concepts": missing_c,
                    "incorrect_claims": incorrect_c,
                    "suggested_improvements": suggested_i,
                })

                question_reviews.append(QuestionReviewItem(
                    sequence_number=q.sequence_number,
                    question_text=q.question_text,
                    competency_name=q.competency.name if q.competency else "Core",
                    difficulty=q.difficulty,
                    question_type=q.question_type,
                    answer_text=ans.answer_text if ans else "",
                    weighted_score=ev.weighted_score,
                    relevance_score=ev.relevance_score,
                    technical_score=ev.technical_score,
                    completeness_score=ev.completeness_score,
                    communication_score=ev.communication_score,
                    semantic_similarity=ev.semantic_similarity,
                    correct_concepts=correct_c,
                    missing_concepts=missing_c,
                    suggested_improvements=suggested_i,
                ))

        # Aggregate finalized scores
        score_data = scoring_service.aggregate_session_scores(
            session=session,
            competencies=competencies,
            questions=questions,
            evaluations_by_question_id=evaluations_by_q_id,
            is_final=True
        )

        overall_score = score_data["overall_score"]
        dim_scores = score_data["dimension_scores"]
        comp_scores = score_data["competency_scores"]

        # Generate evidence-linked feedback
        feedback_dict = feedback_service.generate_feedback(
            job_role=session.job_role,
            overall_score=overall_score,
            dimension_scores=dim_scores,
            competency_scores=comp_scores,
            question_evaluations=question_eval_summaries
        )

        tested_comps = [c for c in comp_scores if c.get("questions_tested", 0) > 0]
        tested_comps.sort(key=lambda x: x["score"], reverse=True)
        strongest = [c["name"] for c in tested_comps if c["score"] >= 70][:3]
        weakest = [c["name"] for c in tested_comps if c["score"] < 70][:3]

        report_payload = {
            "overall_score": overall_score,
            "performance_summary": feedback_dict.get("performance_summary", ""),
            "dimension_scores": dim_scores,
            "competency_scores": comp_scores,
            "strongest_competencies": strongest,
            "weakest_competencies": weakest,
            "answered_count": score_data["answered_count"],
            "skipped_count": score_data["skipped_count"],
            "coverage_pct": score_data["coverage_pct"],
            "difficulty_distribution": difficulty_distribution,
            "question_reviews": [qr.model_dump() for qr in question_reviews],
            "feedback": feedback_dict,
        }

        # Check if report already exists for this session
        existing_report = db.query(SessionReport).filter(SessionReport.session_id == session_id).first()
        if existing_report:
            existing_report.overall_score = overall_score
            existing_report.relevance_avg = dim_scores.get("relevance", 0.0)
            existing_report.technical_avg = dim_scores.get("technical", 0.0)
            existing_report.completeness_avg = dim_scores.get("completeness", 0.0)
            existing_report.communication_avg = dim_scores.get("communication", 0.0)
            existing_report.competency_scores_json = json.dumps(comp_scores)
            existing_report.category_scores_json = json.dumps(score_data["category_scores"])
            existing_report.feedback_json = json.dumps(feedback_dict)
            existing_report.report_json = json.dumps(report_payload)
            existing_report.generated_at = datetime.utcnow()
            report_record = existing_report
        else:
            report_record = SessionReport(
                session_id=session_id,
                overall_score=overall_score,
                relevance_avg=dim_scores.get("relevance", 0.0),
                technical_avg=dim_scores.get("technical", 0.0),
                completeness_avg=dim_scores.get("completeness", 0.0),
                communication_avg=dim_scores.get("communication", 0.0),
                competency_scores_json=json.dumps(comp_scores),
                category_scores_json=json.dumps(score_data["category_scores"]),
                feedback_json=json.dumps(feedback_dict),
                report_json=json.dumps(report_payload),
                generated_at=datetime.utcnow()
            )
            db.add(report_record)

        # Mark session as completed
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(report_record)

        return SessionReportResponse(
            id=report_record.id,
            session_id=session_id,
            job_role=session.job_role,
            overall_score=overall_score,
            performance_summary=feedback_dict.get("performance_summary", ""),
            dimension_scores=DimensionScores(
                relevance=dim_scores.get("relevance", 0.0),
                technical_correctness=dim_scores.get("technical", 0.0),
                completeness=dim_scores.get("completeness", 0.0),
                communication=dim_scores.get("communication", 0.0),
            ),
            competency_scores=comp_scores,
            strongest_competencies=strongest,
            weakest_competencies=weakest,
            answered_count=score_data["answered_count"],
            skipped_count=score_data["skipped_count"],
            coverage_pct=score_data["coverage_pct"],
            difficulty_distribution=difficulty_distribution,
            question_reviews=question_reviews,
            feedback=FeedbackReport(**feedback_dict),
            generated_at=report_record.generated_at,
        )


report_service = ReportService()
