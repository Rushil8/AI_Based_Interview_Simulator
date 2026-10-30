import json
import re
from typing import Dict, Any, List
from google import genai
from google.genai import types
from app.config import settings
from app.prompts.feedback_prompt import FEEDBACK_SYSTEM_INSTRUCTION, build_feedback_prompt


class FeedbackService:
    def __init__(self):
        self.client = None
        if settings.GEMINI_API_KEY and not settings.MOCK_AI:
            try:
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception as e:
                print(f"Failed to initialize Gemini Client for feedback: {e}")
                self.client = None

    def generate_feedback(
        self,
        job_role: str,
        overall_score: float,
        dimension_scores: Dict[str, float],
        competency_scores: List[Dict[str, Any]],
        question_evaluations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Synthesizes evaluated question answers, missed concepts, and competency performance
        into personalized, evidence-linked feedback and action plan.
        """
        if self.client and not settings.MOCK_AI:
            try:
                return self._generate_with_gemini(
                    job_role,
                    overall_score,
                    dimension_scores,
                    competency_scores,
                    question_evaluations
                )
            except Exception as e:
                print(f"Gemini Feedback Generation failed: {e}. Falling back to deterministic synthesizer.")

        return self._generate_deterministic_feedback(
            job_role,
            overall_score,
            dimension_scores,
            competency_scores,
            question_evaluations
        )

    def _generate_with_gemini(
        self,
        job_role: str,
        overall_score: float,
        dimension_scores: Dict[str, float],
        competency_scores: List[Dict[str, Any]],
        question_evaluations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        prompt = build_feedback_prompt(
            job_role=job_role,
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            competency_scores=competency_scores,
            evaluated_questions_summary=question_evaluations
        )

        response = self.client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=FEEDBACK_SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                temperature=0.3,
            ),
        )

        raw_json = response.text
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw_json.strip())
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return json.loads(cleaned)

    def _generate_deterministic_feedback(
        self,
        job_role: str,
        overall_score: float,
        dimension_scores: Dict[str, float],
        competency_scores: List[Dict[str, Any]],
        question_evaluations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Evidence-linked feedback generator based directly on candidate's answers and evaluations.
        """
        # Collect all correct concepts and missed concepts across evaluations
        all_correct = []
        all_missing = []
        all_improvements = []

        for qe in question_evaluations:
            all_correct.extend(qe.get("correct_concepts", []))
            all_missing.extend(qe.get("missing_concepts", []))
            all_improvements.extend(qe.get("suggested_improvements", []))

        # Rank competencies
        tested_comps = [c for c in competency_scores if c.get("questions_tested", 0) > 0]
        tested_comps.sort(key=lambda x: x["score"], reverse=True)

        strong_comps = [c["name"] for c in tested_comps if c["score"] >= 75]
        weak_comps = [c["name"] for c in tested_comps if c["score"] < 70]

        if overall_score >= 80:
            summary = (
                f"Exceptional preparation for the {job_role} position. Demonstrated comprehensive architectural "
                f"insight, precise terminology, and strong grasp of core engineering principles."
            )
        elif overall_score >= 60:
            summary = (
                f"Solid foundational competence for the {job_role} role. Handled primary questions effectively, "
                f"with clear growth opportunities in edge cases, scale trade-offs, and deeper technical nuances."
            )
        else:
            summary = (
                f"Emerging preparation for {job_role}. Key concepts require revision before live interviews, "
                f"particularly around systems design, correctness under load, and comprehensive problem breakdown."
            )

        overall_strengths = []
        if strong_comps:
            overall_strengths.append(f"Demonstrated high domain proficiency in: {', '.join(strong_comps[:2])}.")
        if all_correct:
            overall_strengths.append(f"Strong grasp of: '{all_correct[0]}'.")
        if dimension_scores.get("communication", 0) >= 75:
            overall_strengths.append("Structured explanations clearly with professional engineering vocabulary.")

        technical_strengths = []
        for c in tested_comps[:2]:
            if c["score"] >= 65:
                technical_strengths.append(f"Solid understanding of {c['name']} (Scored {c['score']:.1f}%).")

        corrections = []
        for qe in question_evaluations:
            incorrects = qe.get("incorrect_claims", [])
            for inc in incorrects:
                corrections.append(f"Correction on {qe.get('competency_name', 'Topic')}: {inc}")

        comm_improvements = []
        if dimension_scores.get("communication", 0) < 70:
            comm_improvements.append("Use structured answer frameworks like Situation-Task-Action-Result or Point-Reason-Example.")
            comm_improvements.append("State trade-offs upfront before concluding on a single architectural decision.")
        else:
            comm_improvements.append("Maintain the structured, concise delivery demonstrated during this interview session.")

        practice_exercises = [
            f"Build a miniature prototype focusing on {weak_comps[0] if weak_comps else 'Distributed Systems'} to internalize runtime mechanics.",
            f"Practice explaining time/space complexity and failure scenarios out loud under a 3-minute timer."
        ]

        topics_to_revise = list(dict.fromkeys(all_missing[:4]))
        if not topics_to_revise and weak_comps:
            topics_to_revise = [f"{w} Core Patterns & Antipatterns" for w in weak_comps]

        next_steps = [
            f"Review the highlighted missing concepts in {job_role} fundamentals.",
            "Run a timed mock interview focusing on Senior-level architecture questions.",
            "Implement unit and integration testing exercises to cement verification habits."
        ]

        return {
            "performance_summary": summary,
            "overall_strengths": overall_strengths or ["Clear effort to address prompt instructions."],
            "technical_strengths": technical_strengths or ["Foundational awareness of software concepts."],
            "missing_concepts": list(dict.fromkeys(all_missing[:5])),
            "weak_competencies": weak_comps or ["None identified; performance was balanced across tested competencies."],
            "corrections_and_explanations": corrections or ["No major factual inaccuracies identified in provided answers."],
            "communication_improvements": comm_improvements,
            "practice_exercises": practice_exercises,
            "recommended_topics_to_revise": topics_to_revise or ["High-scale concurrency and database indexing."],
            "recommended_next_steps": next_steps,
        }


feedback_service = FeedbackService()
