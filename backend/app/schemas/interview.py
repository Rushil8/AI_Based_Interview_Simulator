from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.question import QuestionPublicResponse


class CompetencyResponse(BaseModel):
    id: str
    name: str
    category: str
    importance_weight: float
    relevance_score: float
    initial_strength: float
    evidence: Optional[str] = None
    coverage_status: str

    model_config = ConfigDict(from_attributes=True)


class InterviewSessionCreate(BaseModel):
    profile_id: str
    job_role: str = Field(..., min_length=2, description="Target job title or role")
    job_description: Optional[str] = Field(None, description="Optional target job description or requirements")
    difficulty: str = Field("mid", description="junior, mid, senior")
    duration_minutes: int = Field(30, ge=10, le=120)
    target_question_count: int = Field(5, ge=3, le=15)


class InterviewSessionResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    profile_id: Optional[str] = None
    job_role: str
    job_description: Optional[str] = None
    status: str
    difficulty: str
    duration_minutes: int
    target_question_count: int
    current_question_index: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    competencies: List[CompetencyResponse] = Field(default_factory=list)
    questions: List[QuestionPublicResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class InterviewProgressResponse(BaseModel):
    session_id: str
    current_question_index: int
    target_question_count: int
    answered_count: int
    remaining_count: int
    provisional_score: Optional[float] = None
    competency_coverage_pct: float
    status: str
    can_proceed: bool


class NextQuestionResponse(BaseModel):
    is_finished: bool
    question: Optional[QuestionPublicResponse] = None
    adaptation_reason: Optional[str] = None
    progress: InterviewProgressResponse
