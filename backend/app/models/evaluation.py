import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid():
    return uuid.uuid4().hex


class AnswerEvaluation(Base):
    __tablename__ = "answer_evaluations"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    answer_id = Column(String(36), ForeignKey("candidate_answers.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    relevance_score = Column(Float, nullable=False)
    technical_score = Column(Float, nullable=False)
    completeness_score = Column(Float, nullable=False)
    communication_score = Column(Float, nullable=False)
    weighted_score = Column(Float, nullable=False)
    
    # Sentence-BERT diagnostic semantic similarity score (0.0 - 1.0)
    semantic_similarity = Column(Float, nullable=False, default=0.0)

    # Stored as JSON strings
    evidence_json = Column(Text, nullable=False)
    correct_concepts_json = Column(Text, nullable=False)
    missing_concepts_json = Column(Text, nullable=False)
    incorrect_claims_json = Column(Text, nullable=False)
    suggested_improvements_json = Column(Text, nullable=False)

    confidence_score = Column(Float, default=0.9, nullable=False)
    rubric_version = Column(String(50), default="v1.0", nullable=False)
    evaluation_status = Column(String(50), default="evaluated", nullable=False)  # evaluated, failed
    evaluated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    answer = relationship("CandidateAnswer", back_populates="evaluation")
