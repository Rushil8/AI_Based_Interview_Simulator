from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class EvaluationDimensionBreakdown(BaseModel):
    score: float
    weight: float
    contribution: float
    criteria: Optional[str] = None
    evidence: Optional[str] = None


class AnswerEvaluationResponse(BaseModel):
    id: str
    answer_id: str
    relevance_score: float
    technical_score: float
    completeness_score: float
    communication_score: float
    weighted_score: float
    semantic_similarity: float

    evidence: Dict[str, str] = Field(default_factory=dict)
    correct_concepts: List[str] = Field(default_factory=list)
    missing_concepts: List[str] = Field(default_factory=list)
    incorrect_claims: List[str] = Field(default_factory=list)
    suggested_improvements: List[str] = Field(default_factory=list)
    
    dimension_breakdown: Optional[Dict[str, EvaluationDimensionBreakdown]] = None
    confidence_score: float = 0.95
    rubric_version: str = "v1.0"
    evaluation_status: str = "evaluated"
    evaluated_at: datetime

    model_config = ConfigDict(from_attributes=True)
