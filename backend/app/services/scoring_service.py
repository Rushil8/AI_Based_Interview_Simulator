from typing import List, Dict, Any, Tuple
from app.models.competency import Competency
from app.models.question import InterviewQuestion
from app.models.evaluation import AnswerEvaluation
from app.models.session import InterviewSession


class ScoringService:
    @staticmethod
    def aggregate_session_scores(
        session: InterviewSession,
        competencies: List[Competency],
        questions: List[InterviewQuestion],
        evaluations_by_question_id: Dict[str, AnswerEvaluation],
        is_final: bool = False
    ) -> Dict[str, Any]:
        """
        Aggregates question scores into competency, category, dimension, and overall scores.
        Clearly distinguishes provisional scores (during session) from final scores (at completion),
        preventing unanswered questions from inflating the final grade.
        """
        total_target_questions = session.target_question_count or 5
        answered_questions = []
        skipped_count = 0

        dimension_totals = {
            "relevance": 0.0,
            "technical": 0.0,
            "completeness": 0.0,
            "communication": 0.0,
        }

        # Map evaluations to competencies
        comp_scores_map: Dict[str, List[float]] = {c.id: [] for c in competencies}

        # Map evaluations to categories (technical, behavioral, etc.)
        cat_scores_map: Dict[str, List[float]] = {}

        for q in questions:
            ev = evaluations_by_question_id.get(q.id)
            if ev and ev.evaluation_status == "evaluated":
                answered_questions.append(q)
                dimension_totals["relevance"] += ev.relevance_score
                dimension_totals["technical"] += ev.technical_score
                dimension_totals["completeness"] += ev.completeness_score
                dimension_totals["communication"] += ev.communication_score

                if q.competency_id and q.competency_id in comp_scores_map:
                    comp_scores_map[q.competency_id].append(ev.weighted_score)

                q_type = q.question_type or "technical"
                if q_type not in cat_scores_map:
                    cat_scores_map[q_type] = []
                cat_scores_map[q_type].append(ev.weighted_score)

        answered_count = len(answered_questions)
        remaining_count = max(0, total_target_questions - answered_count)

        # Dimension Averages
        if answered_count > 0:
            dim_avgs = {
                "relevance": round(dimension_totals["relevance"] / answered_count, 1),
                "technical": round(dimension_totals["technical"] / answered_count, 1),
                "completeness": round(dimension_totals["completeness"] / answered_count, 1),
                "communication": round(dimension_totals["communication"] / answered_count, 1),
            }
        else:
            dim_avgs = {"relevance": 0.0, "technical": 0.0, "completeness": 0.0, "communication": 0.0}

        # Competency Performance Breakdown
        competency_results = []
        weighted_comp_sum = 0.0
        total_active_weight = 0.0

        for comp in competencies:
            scores = comp_scores_map.get(comp.id, [])
            if scores:
                comp_avg = round(sum(scores) / len(scores), 1)
                coverage_status = "covered"
            else:
                comp_avg = round(comp.initial_strength * 60.0, 1) if not is_final else 0.0
                coverage_status = comp.coverage_status

            competency_results.append({
                "competency_id": comp.id,
                "name": comp.name,
                "category": comp.category,
                "score": comp_avg,
                "importance_weight": comp.importance_weight,
                "coverage_status": coverage_status,
                "questions_tested": len(scores),
            })

            # For active score calculation:
            if scores:
                weighted_comp_sum += comp_avg * comp.importance_weight
                total_active_weight += comp.importance_weight

        # Overall Interview Score Calculation
        if is_final:
            # If final, factor in completion percentage to prevent uncompleted sessions from scoring 100%
            completion_ratio = min(1.0, answered_count / max(total_target_questions, 1))
            if total_active_weight > 0:
                base_score = weighted_comp_sum / total_active_weight
                # Weighted penalty if fewer questions were answered than requested
                overall_score = round(base_score * completion_ratio, 1)
            else:
                overall_score = 0.0
        else:
            # Provisional score based purely on completed questions
            if total_active_weight > 0:
                overall_score = round(weighted_comp_sum / total_active_weight, 1)
            else:
                overall_score = 0.0

        # Category Scores
        category_results = {}
        for cat, scs in cat_scores_map.items():
            category_results[cat] = round(sum(scs) / len(scs), 1) if scs else 0.0

        # Competency coverage percentage
        covered_count = sum(1 for c in competency_results if c["coverage_status"] in ["covered", "partially_covered"])
        coverage_pct = round((covered_count / max(len(competencies), 1)) * 100, 1)

        completion_pct = round((answered_count / max(total_target_questions, 1)) * 100, 1)

        return {
            "overall_score": overall_score,
            "is_final": is_final,
            "provisional_score": overall_score if not is_final else None,
            "dimension_scores": dim_avgs,
            "competency_scores": competency_results,
            "category_scores": category_results,
            "answered_count": answered_count,
            "skipped_count": skipped_count,
            "remaining_count": remaining_count,
            "target_question_count": total_target_questions,
            "coverage_pct": coverage_pct,
            "completion_pct": completion_pct,
        }


scoring_service = ScoringService()
