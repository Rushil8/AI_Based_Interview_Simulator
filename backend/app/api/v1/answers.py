import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.session import InterviewSession
from app.models.question import InterviewQuestion
from app.models.answer import CandidateAnswer
from app.models.evaluation import AnswerEvaluation
from app.schemas.answer import AnswerSubmitRequest
from app.schemas.evaluation import AnswerEvaluationResponse, EvaluationDimensionBreakdown
from app.services.answer_evaluation_service import answer_evaluation_service
from app.config import settings

router = APIRouter(tags=["Answers"])


@router.post("/interviews/{session_id}/answers", response_model=AnswerEvaluationResponse, status_code=status.HTTP_201_CREATED)
def submit_answer(
    session_id: str,
    payload: AnswerSubmitRequest,
    db: Session = Depends(get_db)
):
    """
    Submits a candidate typed answer.
    CRITICAL RELIABILITY DIRECTIVE: Persists the answer text to DB BEFORE invoking evaluation
    so an external API failure will never erase candidate work.
    Evaluates across 4 rubric dimensions with diagnostic Sentence-BERT similarity.
    """
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found.")

    question = (
        db.query(InterviewQuestion)
        .filter(InterviewQuestion.id == payload.question_id, InterviewQuestion.session_id == session_id)
        .first()
    )
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found in this session.")

    # Check for existing answer (idempotency check)
    existing_answer = (
        db.query(CandidateAnswer)
        .filter(CandidateAnswer.question_id == payload.question_id, CandidateAnswer.session_id == session_id)
        .first()
    )

    if existing_answer:
        answer_rec = existing_answer
        # Update answer text if resubmitted
        answer_rec.answer_text = payload.answer_text
        answer_rec.submitted_at = datetime.utcnow()
    else:
        # 1. PERSIST SUBMITTED ANSWER FIRST
        answer_rec = CandidateAnswer(
            session_id=session_id,
            question_id=payload.question_id,
            answer_text=payload.answer_text,
            submitted_at=datetime.utcnow()
        )
        db.add(answer_rec)

    db.commit()
    db.refresh(answer_rec)

    # 2. EVALUATE ANSWER
    expected_elements = json.loads(question.expected_elements_json) if question.expected_elements_json else []
    rubric_dict = json.loads(question.rubric_json) if question.rubric_json else {}

    try:
        eval_result = answer_evaluation_service.evaluate_answer(
            question_text=question.question_text,
            question_type=question.question_type,
            difficulty=question.difficulty,
            expected_elements=expected_elements,
            rubric_dict=rubric_dict,
            candidate_answer=payload.answer_text
        )
    except Exception as e:
        # Fallback to failed status evaluation
        eval_result = {
            "relevance_score": 50.0,
            "technical_score": 50.0,
            "completeness_score": 50.0,
            "communication_score": 50.0,
            "weighted_score": 50.0,
            "semantic_similarity": 0.0,
            "evidence": {"evaluation_error": str(e)},
            "correct_concepts": [],
            "missing_concepts": [],
            "incorrect_claims": [],
            "suggested_improvements": ["System had difficulty evaluating answer. Contact administrator."],
            "confidence_score": 0.5,
            "rubric_version": settings.RUBRIC_VERSION,
            "evaluation_status": "failed",
        }

    # 3. SAVE EVALUATION RECORD
    existing_eval = db.query(AnswerEvaluation).filter(AnswerEvaluation.answer_id == answer_rec.id).first()
    if existing_eval:
        eval_record = existing_eval
        eval_record.relevance_score = eval_result["relevance_score"]
        eval_record.technical_score = eval_result["technical_score"]
        eval_record.completeness_score = eval_result["completeness_score"]
        eval_record.communication_score = eval_result["communication_score"]
        eval_record.weighted_score = eval_result["weighted_score"]
        eval_record.semantic_similarity = eval_result["semantic_similarity"]
        eval_record.evidence_json = json.dumps(eval_result["evidence"])
        eval_record.correct_concepts_json = json.dumps(eval_result["correct_concepts"])
        eval_record.missing_concepts_json = json.dumps(eval_result["missing_concepts"])
        eval_record.incorrect_claims_json = json.dumps(eval_result["incorrect_claims"])
        eval_record.suggested_improvements_json = json.dumps(eval_result["suggested_improvements"])
        eval_record.confidence_score = eval_result.get("confidence_score", 0.95)
        eval_record.rubric_version = eval_result.get("rubric_version", settings.RUBRIC_VERSION)
        eval_record.evaluation_status = eval_result.get("evaluation_status", "evaluated")
        eval_record.evaluated_at = datetime.utcnow()
    else:
        eval_record = AnswerEvaluation(
            answer_id=answer_rec.id,
            relevance_score=eval_result["relevance_score"],
            technical_score=eval_result["technical_score"],
            completeness_score=eval_result["completeness_score"],
            communication_score=eval_result["communication_score"],
            weighted_score=eval_result["weighted_score"],
            semantic_similarity=eval_result["semantic_similarity"],
            evidence_json=json.dumps(eval_result["evidence"]),
            correct_concepts_json=json.dumps(eval_result["correct_concepts"]),
            missing_concepts_json=json.dumps(eval_result["missing_concepts"]),
            incorrect_claims_json=json.dumps(eval_result["incorrect_claims"]),
            suggested_improvements_json=json.dumps(eval_result["suggested_improvements"]),
            confidence_score=eval_result.get("confidence_score", 0.95),
            rubric_version=eval_result.get("rubric_version", settings.RUBRIC_VERSION),
            evaluation_status=eval_result.get("evaluation_status", "evaluated"),
            evaluated_at=datetime.utcnow()
        )
        db.add(eval_record)

    # Update competency coverage status
    if question.competency:
        if eval_result["weighted_score"] >= 65:
            question.competency.coverage_status = "covered"
        else:
            question.competency.coverage_status = "partially_covered"

    db.commit()
    db.refresh(eval_record)

    return _serialize_evaluation(eval_record)


@router.get("/answers/{answer_id}/evaluation", response_model=AnswerEvaluationResponse)
def get_answer_evaluation(answer_id: str, db: Session = Depends(get_db)):
    eval_record = db.query(AnswerEvaluation).filter(AnswerEvaluation.answer_id == answer_id).first()
    if not eval_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found for this answer.")
    return _serialize_evaluation(eval_record)


def _serialize_evaluation(record: AnswerEvaluation) -> AnswerEvaluationResponse:
    evidence = json.loads(record.evidence_json) if record.evidence_json else {}
    correct = json.loads(record.correct_concepts_json) if record.correct_concepts_json else []
    missing = json.loads(record.missing_concepts_json) if record.missing_concepts_json else []
    incorrect = json.loads(record.incorrect_claims_json) if record.incorrect_claims_json else []
    suggested = json.loads(record.suggested_improvements_json) if record.suggested_improvements_json else []

    breakdown = {
        "relevance": EvaluationDimensionBreakdown(
            score=record.relevance_score,
            weight=settings.RUBRIC_WEIGHT_RELEVANCE,
            contribution=round(record.relevance_score * settings.RUBRIC_WEIGHT_RELEVANCE, 2),
            evidence=evidence.get("relevance")
        ),
        "technical_correctness": EvaluationDimensionBreakdown(
            score=record.technical_score,
            weight=settings.RUBRIC_WEIGHT_TECHNICAL,
            contribution=round(record.technical_score * settings.RUBRIC_WEIGHT_TECHNICAL, 2),
            evidence=evidence.get("technical")
        ),
        "completeness": EvaluationDimensionBreakdown(
            score=record.completeness_score,
            weight=settings.RUBRIC_WEIGHT_COMPLETENESS,
            contribution=round(record.completeness_score * settings.RUBRIC_WEIGHT_COMPLETENESS, 2),
            evidence=evidence.get("completeness")
        ),
        "communication": EvaluationDimensionBreakdown(
            score=record.communication_score,
            weight=settings.RUBRIC_WEIGHT_COMMUNICATION,
            contribution=round(record.communication_score * settings.RUBRIC_WEIGHT_COMMUNICATION, 2),
            evidence=evidence.get("communication")
        ),
    }

    return AnswerEvaluationResponse(
        id=record.id,
        answer_id=record.answer_id,
        relevance_score=record.relevance_score,
        technical_score=record.technical_score,
        completeness_score=record.completeness_score,
        communication_score=record.communication_score,
        weighted_score=record.weighted_score,
        semantic_similarity=record.semantic_similarity,
        evidence=evidence,
        correct_concepts=correct,
        missing_concepts=missing,
        incorrect_claims=incorrect,
        suggested_improvements=suggested,
        dimension_breakdown=breakdown,
        confidence_score=record.confidence_score,
        rubric_version=record.rubric_version,
        evaluation_status=record.evaluation_status,
        evaluated_at=record.evaluated_at,
    )
