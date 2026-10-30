from typing import List, Dict, Any
from app.models.competency import Competency
from app.models.session import InterviewSession


class PlannedQuestionSlot:
    def __init__(
        self,
        sequence_number: int,
        competency_id: str,
        competency_name: str,
        question_type: str,
        difficulty: str,
        focus_area: str,
    ):
        self.sequence_number = sequence_number
        self.competency_id = competency_id
        self.competency_name = competency_name
        self.question_type = question_type
        self.difficulty = difficulty
        self.focus_area = focus_area

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sequence_number": self.sequence_number,
            "competency_id": self.competency_id,
            "competency_name": self.competency_name,
            "question_type": self.question_type,
            "difficulty": self.difficulty,
            "focus_area": self.focus_area,
        }


class InterviewPlannerService:
    @staticmethod
    def create_interview_plan(
        session: InterviewSession,
        competencies: List[Competency]
    ) -> List[PlannedQuestionSlot]:
        """
        Creates an ordered question budget and strategy.
        Prioritizes high importance + uncovered competencies, balances technical and behavioral,
        and respects target question limit.
        """
        target_count = session.target_question_count or 5
        base_difficulty = session.difficulty or "mid"

        # Sort competencies by priority score:
        # Priority = (importance_weight * 1.5) + (1.0 if uncovered else 0.5 if partially_covered else 0.2)
        def priority_score(c: Competency) -> float:
            uncovered_bonus = 1.0 if c.coverage_status == "uncovered" else (0.5 if c.coverage_status == "partially_covered" else 0.2)
            return (c.importance_weight * 1.5) + uncovered_bonus

        sorted_comps = sorted(competencies, key=priority_score, reverse=True)
        if not sorted_comps:
            raise ValueError("No competencies available to plan interview.")

        plan: List[PlannedQuestionSlot] = []

        # Question types distribution based on target count
        # E.g. for 5 questions:
        # Q1: Technical Core (mid)
        # Q2: Project/Practical Application (mid)
        # Q3: Scenario / Problem Solving (mid/senior)
        # Q4: Technical / Deep Dive (mid)
        # Q5: Behavioral / Collaboration (mid)
        types_cycle = ["technical", "project", "scenario", "problem_solving", "behavioral"]

        for seq in range(1, target_count + 1):
            comp_idx = (seq - 1) % len(sorted_comps)
            comp = sorted_comps[comp_idx]

            q_type = types_cycle[(seq - 1) % len(types_cycle)]
            # If competency is behavioral category, override to behavioral
            if comp.category == "communication" or "collaboration" in comp.name.lower():
                q_type = "behavioral"
            elif comp.category == "problem_solving":
                q_type = "problem_solving"

            # Initial difficulty allocation
            slot_difficulty = base_difficulty
            if seq == 1 and base_difficulty == "senior":
                slot_difficulty = "mid"  # warm-up
            elif seq >= target_count and base_difficulty == "mid":
                slot_difficulty = "mid"

            focus_area = f"Validate {comp.name} with emphasis on {comp.category.replace('_', ' ')}"
            if comp.coverage_status == "uncovered":
                focus_area += " (Uncovered in resume - probe foundational comprehension)"

            slot = PlannedQuestionSlot(
                sequence_number=seq,
                competency_id=comp.id,
                competency_name=comp.name,
                question_type=q_type,
                difficulty=slot_difficulty,
                focus_area=focus_area,
            )
            plan.append(slot)

        return plan


interview_planner_service = InterviewPlannerService()
