import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.profile import CandidateProfile
from app.models.session import InterviewSession
from app.models.competency import Competency
from app.models.question import InterviewQuestion
from app.schemas.profile import StructuredProfile
from app.schemas.interview import (
    InterviewSessionCreate,
    InterviewSessionResponse,
    InterviewProgressResponse,
    NextQuestionResponse,
    CompetencyResponse,
)
from app.schemas.question import QuestionPublicResponse
from app.services.competency_service import competency_service
from app.services.interview_planner_service import interview_planner_service
from app.services.question_generation_service import question_generation_service
from app.services.adaptive_controller_service import adaptive_controller_service
from app.services.scoring_service import scoring_service
from app.services.report_service import report_service

router = APIRouter(prefix="/interviews", tags=["Interviews"])


@router.post("", response_model=InterviewSessionResponse, status_code=status.HTTP_201_CREATED)
def create_interview_session(
    payload: InterviewSessionCreate,
    db: Session = Depends(get_db)
):
    """
    Initializes an adaptive interview session:
    1. Loads candidate profile
    2. Maps profile to role competencies via Sentence-BERT embeddings
    3. Generates interview plan
    4. Generates initial question
    """
    profile = db.query(CandidateProfile).filter(CandidateProfile.id == payload.profile_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile not found.")

    structured_data = json.loads(profile.structured_profile_json)
    structured_profile = StructuredProfile(**structured_data)

    # 1. Map Competencies
    comp_dicts = competency_service.generate_and_map_competencies(
        job_role=payload.job_role,
        job_description=payload.job_description,
        profile=structured_profile
    )

    # 2. Create Interview Session Record
    session = InterviewSession(
        user_id=profile.user_id,
        profile_id=profile.id,
        job_role=payload.job_role,
        job_description=payload.job_description,
        status="in_progress",
        difficulty=payload.difficulty,
        duration_minutes=payload.duration_minutes,
        target_question_count=payload.target_question_count,
        current_question_index=1,
        started_at=datetime.utcnow(),
    )
    db.add(session)
    db.flush()

    # 3. Create Competencies Records
    competency_records = []
    for cd in comp_dicts:
        comp_rec = Competency(
            session_id=session.id,
            name=cd["name"],
            category=cd["category"],
            importance_weight=cd["importance_weight"],
            relevance_score=cd["relevance_score"],
            initial_strength=cd["initial_strength"],
            evidence=cd["evidence"],
            coverage_status=cd["coverage_status"],
        )
        db.add(comp_rec)
        competency_records.append(comp_rec)
    db.flush()

    # 4. Generate Interview Plan
    plan = interview_planner_service.create_interview_plan(session, competency_records)
    first_slot = plan[0]

    # 5. Generate First Question
    q1_data = question_generation_service.generate_question(
        job_role=payload.job_role,
        job_description=payload.job_description,
        competency_id=first_slot.competency_id,
        competency_name=first_slot.competency_name,
        competency_category="technical",
        difficulty=first_slot.difficulty,
        question_type=first_slot.question_type,
        sequence_number=1,
        candidate_profile_json=profile.structured_profile_json,
        previous_questions=[],
        adaptation_reason="Opening question targeting primary role competency."
    )

    first_question = InterviewQuestion(
        session_id=session.id,
        competency_id=first_slot.competency_id,
        sequence_number=1,
        question_text=q1_data["question_text"],
        question_type=q1_data["question_type"],
        difficulty=q1_data["difficulty"],
        expected_elements_json=json.dumps(q1_data["expected_elements"]),
        rubric_json=json.dumps(q1_data["rubric"]),
        maximum_score=q1_data["maximum_score"],
        follow_up_guidance=q1_data.get("follow_up_guidance"),
        is_adaptive_followup=False,
        adaptation_reason="Initial planned question",
    )
    db.add(first_question)
    db.commit()
    db.refresh(session)

    return _serialize_session(session)


@router.get("/{session_id}", response_model=InterviewSessionResponse)
def get_interview_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found.")
    return _serialize_session(session)


@router.get("/{session_id}/current-question", response_model=QuestionPublicResponse)
def get_current_question(session_id: str, db: Session = Depends(get_db)):
    """
    Returns the current active question for the candidate to answer.
    Rubric criteria and ideal answers are strictly excluded to preserve interview integrity.
    """
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found.")

    curr_idx = session.current_question_index
    question = (
        db.query(InterviewQuestion)
        .filter(InterviewQuestion.session_id == session_id, InterviewQuestion.sequence_number == curr_idx)
        .first()
    )

    if not question:
        # Fallback to the latest question created
        question = (
            db.query(InterviewQuestion)
            .filter(InterviewQuestion.session_id == session_id)
            .order_by(InterviewQuestion.sequence_number.desc())
            .first()
        )
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No questions found for this session.")

    return QuestionPublicResponse(
        id=question.id,
        session_id=question.session_id,
        competency_id=question.competency_id,
        competency_name=question.competency.name if question.competency else "Core Engineering",
        sequence_number=question.sequence_number,
        question_text=question.question_text,
        question_type=question.question_type,
        difficulty=question.difficulty,
        maximum_score=question.maximum_score,
        is_adaptive_followup=question.is_adaptive_followup,
        adaptation_reason=question.adaptation_reason,
    )


@router.post("/{session_id}/next-question", response_model=NextQuestionResponse)
def advance_to_next_question(session_id: str, db: Session = Depends(get_db)):
    """
    Adaptive Next-Question Controller:
    Inspects previous answer evaluations, updates difficulty and priority competencies,
    and returns either the next tailored question or marks the session ready for completion.
    """
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found.")

    competencies = session.competencies
    questions = (
        db.query(InterviewQuestion)
        .filter(InterviewQuestion.session_id == session_id)
        .order_by(InterviewQuestion.sequence_number.asc())
        .all()
    )

    evaluations_by_q_id = {}
    for q in questions:
        if q.answers and q.answers[0].evaluation:
            evaluations_by_q_id[q.id] = q.answers[0].evaluation

    # If the last question was NOT answered yet, return it rather than generating a new one
    if questions and questions[-1].id not in evaluations_by_q_id:
        unanswered_q = questions[-1]
        progress_info = _get_progress_info(session, competencies, questions, evaluations_by_q_id)
        return NextQuestionResponse(
            is_finished=False,
            question=QuestionPublicResponse(
                id=unanswered_q.id,
                session_id=unanswered_q.session_id,
                competency_id=unanswered_q.competency_id,
                competency_name=unanswered_q.competency.name if unanswered_q.competency else "Core",
                sequence_number=unanswered_q.sequence_number,
                question_text=unanswered_q.question_text,
                question_type=unanswered_q.question_type,
                difficulty=unanswered_q.difficulty,
                maximum_score=unanswered_q.maximum_score,
                is_adaptive_followup=unanswered_q.is_adaptive_followup,
                adaptation_reason=unanswered_q.adaptation_reason,
            ),
            adaptation_reason=unanswered_q.adaptation_reason,
            progress=progress_info
        )

    # Adaptive decision
    decision = adaptive_controller_service.evaluate_next_step(
        session=session,
        competencies=competencies,
        asked_questions=questions,
        evaluations_by_question_id=evaluations_by_q_id
    )

    if decision.is_finished:
        progress_info = _get_progress_info(session, competencies, questions, evaluations_by_q_id)
        return NextQuestionResponse(
            is_finished=True,
            question=None,
            adaptation_reason=decision.adaptation_reason,
            progress=progress_info
        )

    # Generate the next adaptive question
    next_seq = len(questions) + 1
    profile_json = session.profile.structured_profile_json if session.profile else "{}"

    prev_q_dicts = [{"question_text": q.question_text} for q in questions]

    # Gather previous answer and evaluation context for adaptive follow-up
    last_answer_context = None
    if questions:
        last_question = questions[-1]
        last_eval = evaluations_by_q_id.get(last_question.id)
        last_answer_text = ""
        if last_question.answers:
            last_answer_text = last_question.answers[0].answer_text

        if last_eval and last_answer_text:
            missing_concepts_list = []
            if last_eval.missing_concepts_json:
                try:
                    missing_concepts_list = json.loads(last_eval.missing_concepts_json)
                except Exception:
                    pass

            last_answer_context = {
                "question_text": last_question.question_text,
                "answer_text": last_answer_text,
                "score": last_eval.weighted_score,
                "technical_score": last_eval.technical_score,
                "missing_concepts": missing_concepts_list
            }

    q_data = question_generation_service.generate_question(
        job_role=session.job_role,
        job_description=session.job_description,
        competency_id=decision.competency_id,
        competency_name=decision.competency_name,
        competency_category=decision.competency_category or "technical",
        difficulty=decision.next_difficulty,
        question_type=decision.next_question_type,
        sequence_number=next_seq,
        candidate_profile_json=profile_json,
        previous_questions=prev_q_dicts,
        adaptation_reason=decision.adaptation_reason,
        previous_answer_context=last_answer_context
    )

    new_q = InterviewQuestion(
        session_id=session.id,
        competency_id=decision.competency_id,
        sequence_number=next_seq,
        question_text=q_data["question_text"],
        question_type=q_data["question_type"],
        difficulty=q_data["difficulty"],
        expected_elements_json=json.dumps(q_data["expected_elements"]),
        rubric_json=json.dumps(q_data["rubric"]),
        maximum_score=q_data["maximum_score"],
        follow_up_guidance=q_data.get("follow_up_guidance"),
        is_adaptive_followup=decision.is_adaptive_followup,
        adaptation_reason=decision.adaptation_reason,
    )
    db.add(new_q)
    session.current_question_index = next_seq
    db.commit()
    db.refresh(new_q)

    # Updated questions list
    questions.append(new_q)
    progress_info = _get_progress_info(session, competencies, questions, evaluations_by_q_id)

    return NextQuestionResponse(
        is_finished=False,
        question=QuestionPublicResponse(
            id=new_q.id,
            session_id=new_q.session_id,
            competency_id=new_q.competency_id,
            competency_name=new_q.competency.name if new_q.competency else decision.competency_name,
            sequence_number=new_q.sequence_number,
            question_text=new_q.question_text,
            question_type=new_q.question_type,
            difficulty=new_q.difficulty,
            maximum_score=new_q.maximum_score,
            is_adaptive_followup=new_q.is_adaptive_followup,
            adaptation_reason=new_q.adaptation_reason,
        ),
        adaptation_reason=decision.adaptation_reason,
        progress=progress_info
    )


@router.get("/{session_id}/progress", response_model=InterviewProgressResponse)
def get_interview_progress(session_id: str, db: Session = Depends(get_db)):
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found.")

    competencies = session.competencies
    questions = (
        db.query(InterviewQuestion)
        .filter(InterviewQuestion.session_id == session_id)
        .order_by(InterviewQuestion.sequence_number.asc())
        .all()
    )

    evaluations_by_q_id = {}
    for q in questions:
        if q.answers and q.answers[0].evaluation:
            evaluations_by_q_id[q.id] = q.answers[0].evaluation

    return _get_progress_info(session, competencies, questions, evaluations_by_q_id)


@router.post("/{session_id}/complete")
def complete_interview(session_id: str, db: Session = Depends(get_db)):
    """
    Finalizes the interview, triggers report generation, and updates session status.
    """
    try:
        report_res = report_service.generate_and_save_session_report(db, session_id)
        return report_res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate report: {str(e)}")


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interview(session_id: str, db: Session = Depends(get_db)):
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found.")
    db.delete(session)
    db.commit()
    return None


def _get_progress_info(
    session: InterviewSession,
    competencies: List[Competency],
    questions: List[InterviewQuestion],
    evaluations_by_q_id: dict
) -> InterviewProgressResponse:
    score_data = scoring_service.aggregate_session_scores(
        session=session,
        competencies=competencies,
        questions=questions,
        evaluations_by_question_id=evaluations_by_q_id,
        is_final=False
    )
    answered_count = score_data["answered_count"]
    target_count = session.target_question_count or 5

    # Can proceed if the current question has been answered
    can_proceed = (answered_count >= len(questions))

    return InterviewProgressResponse(
        session_id=session.id,
        current_question_index=session.current_question_index,
        target_question_count=target_count,
        answered_count=answered_count,
        remaining_count=score_data["remaining_count"],
        provisional_score=score_data["provisional_score"],
        competency_coverage_pct=score_data["coverage_pct"],
        status=session.status,
        can_proceed=can_proceed,
    )


def _serialize_session(session: InterviewSession) -> InterviewSessionResponse:
    comps = [
        CompetencyResponse(
            id=c.id,
            name=c.name,
            category=c.category,
            importance_weight=c.importance_weight,
            relevance_score=c.relevance_score,
            initial_strength=c.initial_strength,
            evidence=c.evidence,
            coverage_status=c.coverage_status,
        )
        for c in session.competencies
    ]
    qs = [
        QuestionPublicResponse(
            id=q.id,
            session_id=q.session_id,
            competency_id=q.competency_id,
            competency_name=q.competency.name if q.competency else "Core",
            sequence_number=q.sequence_number,
            question_text=q.question_text,
            question_type=q.question_type,
            difficulty=q.difficulty,
            maximum_score=q.maximum_score,
            is_adaptive_followup=q.is_adaptive_followup,
            adaptation_reason=q.adaptation_reason,
        )
        for q in session.questions
    ]
    return InterviewSessionResponse(
        id=session.id,
        user_id=session.user_id,
        profile_id=session.profile_id,
        job_role=session.job_role,
        job_description=session.job_description,
        status=session.status,
        difficulty=session.difficulty,
        duration_minutes=session.duration_minutes,
        target_question_count=session.target_question_count,
        current_question_index=session.current_question_index,
        started_at=session.started_at,
        completed_at=session.completed_at,
        competencies=comps,
        questions=qs,
    )
