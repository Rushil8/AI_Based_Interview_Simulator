from typing import List, Dict, Any, Optional, Tuple
from app.config import settings
from app.models.competency import Competency
from app.models.question import InterviewQuestion
from app.models.evaluation import AnswerEvaluation
from app.models.session import InterviewSession


class AdaptiveDecision:
    def __init__(
        self,
        is_finished: bool,
        competency_id: Optional[str] = None,
        competency_name: Optional[str] = None,
        competency_category: Optional[str] = None,
        next_difficulty: str = "mid",
        next_question_type: str = "technical",
        is_adaptive_followup: bool = False,
        adaptation_reason: str = "Standard progression",
    ):
        self.is_finished = is_finished
        self.competency_id = competency_id
        self.competency_name = competency_name
        self.competency_category = competency_category
        self.next_difficulty = next_difficulty
        self.next_question_type = next_question_type
        self.is_adaptive_followup = is_adaptive_followup
        self.adaptation_reason = adaptation_reason


class AdaptiveControllerService:
    @staticmethod
    def evaluate_next_step(
        session: InterviewSession,
        competencies: List[Competency],
        asked_questions: List[InterviewQuestion],
        evaluations_by_question_id: Dict[str, AnswerEvaluation],
    ) -> AdaptiveDecision:
        """
        Determines the next adaptive interview step or signals session completion.
        Enforces maximum question budget, avoids infinite loops, and adjusts difficulty
        and competency focus dynamically based on candidate performance.
        """
        target_count = session.target_question_count or 5
        current_asked_count = len(asked_questions)

        # 1. Budget exhausted check
        if current_asked_count >= target_count:
            return AdaptiveDecision(
                is_finished=True,
                adaptation_reason="Interview target question limit reached."
            )

        # Count questions asked per competency to prevent monopolizing single topic
        questions_per_comp: Dict[str, int] = {c.id: 0 for c in competencies}
        for q in asked_questions:
            if q.competency_id in questions_per_comp:
                questions_per_comp[q.competency_id] += 1

        # Look at last evaluated question
        last_q = asked_questions[-1] if asked_questions else None
        last_eval = evaluations_by_question_id.get(last_q.id) if last_q else None

        base_difficulty = session.difficulty or "mid"
        current_difficulty = last_q.difficulty if last_q else base_difficulty

        # If no questions asked yet, start with first planned competency
        if not last_q or not last_eval:
            first_comp = competencies[0] if competencies else None
            return AdaptiveDecision(
                is_finished=False,
                competency_id=first_comp.id if first_comp else None,
                competency_name=first_comp.name if first_comp else "Core Engineering",
                competency_category=first_comp.category if first_comp else "technical",
                next_difficulty=base_difficulty,
                next_question_type="technical",
                is_adaptive_followup=False,
                adaptation_reason="Initial opening question for target role."
            )

        last_weighted = last_eval.weighted_score
        last_tech = last_eval.technical_score
        last_comp_id = last_q.competency_id

        # RULE A: FOUNDATIONAL FOLLOW-UP (Remediation)
        # If low technical score (< 55) and we haven't already repeated this competency
        if last_tech < settings.LOW_SCORE_THRESHOLD and questions_per_comp.get(last_comp_id, 0) < 2:
            next_diff = "junior" if current_difficulty in ["mid", "senior"] else "junior"
            return AdaptiveDecision(
                is_finished=False,
                competency_id=last_comp_id,
                competency_name=last_q.competency.name if last_q.competency else "Technical Core",
                competency_category="technical",
                next_difficulty=next_diff,
                next_question_type="technical",
                is_adaptive_followup=True,
                adaptation_reason=f"Previous technical score was low ({last_tech:.1f}). Shifting to foundational principles to test core fundamentals.",
            )

        # RULE B: ADVANCED ESCALATION
        # If outstanding performance (>= 80), step up difficulty if not already senior
        if last_weighted >= settings.HIGH_SCORE_THRESHOLD:
            next_diff = "senior" if current_difficulty == "mid" else ("mid" if current_difficulty == "junior" else "senior")
            adaptation_note = f"Previous answer scored high ({last_weighted:.1f}). Escalating difficulty to '{next_diff}' to test architectural depth."
        elif last_weighted < settings.LOW_SCORE_THRESHOLD:
            next_diff = "junior" if current_difficulty == "mid" else ("junior" if current_difficulty == "junior" else "mid")
            adaptation_note = f"Adapting difficulty to '{next_diff}' to find candidate comfort level."
        else:
            next_diff = current_difficulty
            adaptation_note = f"Maintaining current difficulty '{next_diff}' for balanced assessment."

        # RULE C: SELECT NEXT COMPETENCY
        # Prioritize important uncovered competencies with 0 questions asked
        uncovered_comps = [c for c in competencies if questions_per_comp.get(c.id, 0) == 0]
        if uncovered_comps:
            # Sort uncovered by importance weight
            uncovered_comps.sort(key=lambda x: x.importance_weight, reverse=True)
            chosen_comp = uncovered_comps[0]
            
            # Select question type based on competency category
            q_type = "technical"
            if chosen_comp.category == "communication":
                q_type = "behavioral"
            elif chosen_comp.category == "problem_solving":
                q_type = "problem_solving"
            elif chosen_comp.category == "system_design":
                q_type = "scenario"

            return AdaptiveDecision(
                is_finished=False,
                competency_id=chosen_comp.id,
                competency_name=chosen_comp.name,
                competency_category=chosen_comp.category,
                next_difficulty=next_diff,
                next_question_type=q_type,
                is_adaptive_followup=False,
                adaptation_reason=f"{adaptation_note} Probing uncovered priority competency: '{chosen_comp.name}'."
            )

        # If all competencies have at least 1 question, pick competency with fewest questions
        sorted_by_count = sorted(competencies, key=lambda c: (questions_per_comp.get(c.id, 0), -c.importance_weight))
        chosen_comp = sorted_by_count[0]

        return AdaptiveDecision(
            is_finished=False,
            competency_id=chosen_comp.id,
            competency_name=chosen_comp.name,
            competency_category=chosen_comp.category,
            next_difficulty=next_diff,
            next_question_type="scenario",
            is_adaptive_followup=False,
            adaptation_reason=f"{adaptation_note} Broadening depth on '{chosen_comp.name}'."
        )


adaptive_controller_service = AdaptiveControllerService()
