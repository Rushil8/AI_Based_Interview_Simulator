from app.services.answer_evaluation_service import answer_evaluation_service
from app.services.scoring_service import scoring_service
from app.config import settings
from app.models.session import InterviewSession
from app.models.competency import Competency
from app.models.question import InterviewQuestion
from app.models.evaluation import AnswerEvaluation


def test_rubric_weights_sum_to_one():
    total = (
        settings.RUBRIC_WEIGHT_RELEVANCE
        + settings.RUBRIC_WEIGHT_TECHNICAL
        + settings.RUBRIC_WEIGHT_COMPLETENESS
        + settings.RUBRIC_WEIGHT_COMMUNICATION
    )
    assert abs(total - 1.0) < 0.001


def test_question_score_formula():
    rel = 80.0
    tech = 90.0
    comp = 70.0
    comm = 85.0

    # Expected: (80*0.20) + (90*0.40) + (70*0.25) + (85*0.15)
    # = 16.0 + 36.0 + 17.5 + 12.75 = 82.25
    expected = (80.0 * 0.20) + (90.0 * 0.40) + (70.0 * 0.25) + (85.0 * 0.15)
    calculated = answer_evaluation_service.calculate_weighted_score(rel, tech, comp, comm)
    assert abs(calculated - round(expected, 2)) < 0.01


def test_session_score_aggregation_provisional_vs_final():
    session = InterviewSession(
        job_role="Full Stack Engineer",
        target_question_count=4,
        difficulty="mid"
    )

    c1 = Competency(id="c1", session_id="s1", name="Frontend", importance_weight=1.0, coverage_status="uncovered", initial_strength=0.5)
    c2 = Competency(id="c2", session_id="s1", name="Backend", importance_weight=1.0, coverage_status="uncovered", initial_strength=0.5)

    q1 = InterviewQuestion(id="q1", sequence_number=1, competency_id="c1", question_text="React state", difficulty="mid")
    q2 = InterviewQuestion(id="q2", sequence_number=2, competency_id="c2", question_text="FastAPI routers", difficulty="mid")

    eval1 = AnswerEvaluation(
        id="e1",
        answer_id="a1",
        relevance_score=80.0,
        technical_score=80.0,
        completeness_score=80.0,
        communication_score=80.0,
        weighted_score=80.0,
        evaluation_status="evaluated"
    )

    evaluations_map = {"q1": eval1}

    # Provisional score (1 of 4 answered with score 80):
    provisional = scoring_service.aggregate_session_scores(
        session=session,
        competencies=[c1, c2],
        questions=[q1, q2],
        evaluations_by_question_id=evaluations_map,
        is_final=False
    )
    assert provisional["is_final"] is False
    assert provisional["answered_count"] == 1
    assert provisional["overall_score"] == 80.0

    # Final score (only 1 of 4 answered, so completion ratio = 1/4 = 0.25 -> final score = 80 * 0.25 = 20.0):
    final = scoring_service.aggregate_session_scores(
        session=session,
        competencies=[c1, c2],
        questions=[q1, q2],
        evaluations_by_question_id=evaluations_map,
        is_final=True
    )
    assert final["is_final"] is True
    assert final["overall_score"] == 20.0  # Unanswered questions penalize the final score as required!
