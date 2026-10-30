from app.services.adaptive_controller_service import adaptive_controller_service
from app.models.session import InterviewSession
from app.models.competency import Competency
from app.models.question import InterviewQuestion
from app.models.evaluation import AnswerEvaluation


def test_adaptive_escalation_on_high_score():
    session = InterviewSession(job_role="Engineer", target_question_count=4, difficulty="mid")
    c1 = Competency(id="c1", session_id="s1", name="Algorithms", importance_weight=1.0, coverage_status="uncovered", category="technical")
    c2 = Competency(id="c2", session_id="s1", name="Databases", importance_weight=1.0, coverage_status="uncovered", category="technical")

    q1 = InterviewQuestion(id="q1", sequence_number=1, competency_id="c1", difficulty="mid", competency=c1)
    ev1 = AnswerEvaluation(answer_id="a1", weighted_score=88.0, technical_score=90.0, evaluation_status="evaluated")

    decision = adaptive_controller_service.evaluate_next_step(
        session=session,
        competencies=[c1, c2],
        asked_questions=[q1],
        evaluations_by_question_id={"q1": ev1}
    )

    assert decision.is_finished is False
    assert decision.next_difficulty == "senior"  # Escalates from mid to senior
    assert decision.competency_id == "c2"  # Prioritizes uncovered competency


def test_adaptive_remediation_on_low_score():
    session = InterviewSession(job_role="Engineer", target_question_count=4, difficulty="mid")
    c1 = Competency(id="c1", session_id="s1", name="Distributed Systems", importance_weight=1.0, coverage_status="uncovered", category="technical")
    c2 = Competency(id="c2", session_id="s1", name="Security", importance_weight=1.0, coverage_status="uncovered", category="technical")

    q1 = InterviewQuestion(id="q1", sequence_number=1, competency_id="c1", difficulty="mid", competency=c1)
    ev1 = AnswerEvaluation(answer_id="a1", weighted_score=45.0, technical_score=40.0, evaluation_status="evaluated")

    decision = adaptive_controller_service.evaluate_next_step(
        session=session,
        competencies=[c1, c2],
        asked_questions=[q1],
        evaluations_by_question_id={"q1": ev1}
    )

    assert decision.is_finished is False
    assert decision.is_adaptive_followup is True
    assert decision.next_difficulty == "junior"  # Remediation step down to foundational


def test_budget_exhaustion_completes_session():
    session = InterviewSession(job_role="Engineer", target_question_count=2, difficulty="mid")
    c1 = Competency(id="c1", session_id="s1", name="DevOps", importance_weight=1.0, coverage_status="uncovered", category="technical")

    q1 = InterviewQuestion(id="q1", sequence_number=1, competency_id="c1", difficulty="mid")
    q2 = InterviewQuestion(id="q2", sequence_number=2, competency_id="c1", difficulty="mid")

    decision = adaptive_controller_service.evaluate_next_step(
        session=session,
        competencies=[c1],
        asked_questions=[q1, q2],
        evaluations_by_question_id={}
    )

    assert decision.is_finished is True
