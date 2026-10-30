from typing import List, Tuple, Optional
from app.config import settings
from app.services.competency_service import competency_service


class SemanticSimilarityService:
    @staticmethod
    def calculate_answer_semantic_similarity(
        question_text: str,
        expected_elements: List[str],
        candidate_answer: str
    ) -> float:
        """
        Calculates Sentence-BERT cosine similarity between candidate typed answer
        and the expected conceptual context (question text + key rubric concepts).
        Returns a normalized score between 0.0 and 1.0.
        """
        if not candidate_answer or not candidate_answer.strip():
            return 0.0

        reference_context = f"{question_text} " + " ".join(expected_elements or [])
        sim = competency_service.compute_similarity(candidate_answer, reference_context)
        return round(float(sim), 4)

    @staticmethod
    def evaluate_diagnostic_signal(
        semantic_similarity: float,
        rubric_relevance_score: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Diagnostic cross-check:
        Flags answers that have extremely low semantic alignment with the question domain.
        Note: Per prompt directives, semantic similarity is treated as a separate diagnostic metric
        and does not override factual/technical correctness or double-count rubric relevance.
        """
        threshold = settings.SEMANTIC_SIMILARITY_FLAG_THRESHOLD  # default 0.50

        if semantic_similarity < (threshold - 0.20):  # e.g. < 0.30
            return (
                True,
                f"Diagnostic Warning: Candidate answer shows very low semantic alignment ({semantic_similarity:.2f}) "
                f"with expected technical concepts. Answer may be off-topic or evasive."
            )
        elif semantic_similarity > 0.85 and rubric_relevance_score < 40.0:
            return (
                True,
                f"Diagnostic Note: High semantic similarity ({semantic_similarity:.2f}) with low rubric relevance "
                f"suggests possible keyword stuffing without addressing the core query."
            )

        return False, None


semantic_similarity_service = SemanticSimilarityService()
