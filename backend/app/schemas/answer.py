from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AnswerSubmitRequest(BaseModel):
    question_id: str
    answer_text: str = Field(..., min_length=1, description="Candidate typed answer text")


class AnswerResponse(BaseModel):
    id: str
    session_id: str
    question_id: str
    answer_text: str
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)
