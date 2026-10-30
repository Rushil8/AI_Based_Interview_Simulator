from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EvaluationRubric(BaseModel):
    relevance_criteria: str = "Addresses the question asked directly without unnecessary digressions."
    technical_criteria: str = "Demonstrates correct principles, syntax, patterns, and architectural awareness."
    completeness_criteria: str = "Explains core steps, edge cases, and reasoning thoroughly."
    communication_criteria: str = "Structure is clear, terminology is precise, and explanation is cohesive."


class QuestionPublicResponse(BaseModel):
    id: str
    session_id: str
    competency_id: Optional[str] = None
    competency_name: Optional[str] = None
    sequence_number: int
    question_text: str
    question_type: str
    difficulty: str
    maximum_score: float = 100.0
    is_adaptive_followup: bool = False
    adaptation_reason: Optional[str] = None


class QuestionFullResponse(QuestionPublicResponse):
    expected_elements: List[str] = Field(default_factory=list)
    rubric: EvaluationRubric = Field(default_factory=EvaluationRubric)
    follow_up_guidance: Optional[str] = None
