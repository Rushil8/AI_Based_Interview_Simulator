from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CompetencyPerformance(BaseModel):
    competency_id: str
    name: str
    category: str
    score: float
    importance_weight: float
    coverage_status: str
    questions_tested: int


class DimensionScores(BaseModel):
    relevance: float
    technical_correctness: float
    completeness: float
    communication: float


class QuestionReviewItem(BaseModel):
    sequence_number: int
    question_text: str
    competency_name: str
    difficulty: str
    question_type: str
    answer_text: str
    weighted_score: float
    relevance_score: float
    technical_score: float
    completeness_score: float
    communication_score: float
    semantic_similarity: float
    correct_concepts: List[str] = Field(default_factory=list)
    missing_concepts: List[str] = Field(default_factory=list)
    suggested_improvements: List[str] = Field(default_factory=list)


class FeedbackReport(BaseModel):
    overall_strengths: List[str] = Field(default_factory=list)
    technical_strengths: List[str] = Field(default_factory=list)
    missing_concepts: List[str] = Field(default_factory=list)
    weak_competencies: List[str] = Field(default_factory=list)
    corrections_and_explanations: List[str] = Field(default_factory=list)
    communication_improvements: List[str] = Field(default_factory=list)
    practice_exercises: List[str] = Field(default_factory=list)
    recommended_topics_to_revise: List[str] = Field(default_factory=list)
    recommended_next_steps: List[str] = Field(default_factory=list)


class SessionReportResponse(BaseModel):
    id: str
    session_id: str
    job_role: str
    overall_score: float
    performance_summary: str
    dimension_scores: DimensionScores
    competency_scores: List[CompetencyPerformance] = Field(default_factory=list)
    strongest_competencies: List[str] = Field(default_factory=list)
    weakest_competencies: List[str] = Field(default_factory=list)
    answered_count: int
    skipped_count: int
    coverage_pct: float
    difficulty_distribution: Dict[str, int] = Field(default_factory=dict)
    question_reviews: List[QuestionReviewItem] = Field(default_factory=list)
    feedback: FeedbackReport
    hiring_disclaimer: str = (
        "Notice: This assessment is an automated AI-assisted practice and preparation tool. "
        "Scores and analytics reflect practice simulations and rubric evaluations, and do not constitute "
        "a guarantee or prediction of actual hiring outcomes or employment decisions by any employer."
    )
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)
