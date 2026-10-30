import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid():
    return uuid.uuid4().hex


class SessionReport(Base):
    __tablename__ = "session_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    session_id = Column(String(36), ForeignKey("interview_sessions.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    overall_score = Column(Float, nullable=False)
    relevance_avg = Column(Float, nullable=False, default=0.0)
    technical_avg = Column(Float, nullable=False, default=0.0)
    completeness_avg = Column(Float, nullable=False, default=0.0)
    communication_avg = Column(Float, nullable=False, default=0.0)

    # Stored as JSON strings
    competency_scores_json = Column(Text, nullable=False)
    category_scores_json = Column(Text, nullable=False)
    feedback_json = Column(Text, nullable=False)
    report_json = Column(Text, nullable=False)

    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("InterviewSession", back_populates="report")
