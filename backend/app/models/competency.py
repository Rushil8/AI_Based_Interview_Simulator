import uuid
from sqlalchemy import Column, String, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid():
    return uuid.uuid4().hex


class Competency(Base):
    __tablename__ = "competencies"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    session_id = Column(String(36), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(150), nullable=False)
    category = Column(String(50), default="technical", nullable=False)  # technical, behavioral, system_design, problem_solving
    importance_weight = Column(Float, default=1.0, nullable=False)
    relevance_score = Column(Float, default=0.8, nullable=False)
    initial_strength = Column(Float, default=0.5, nullable=False)
    evidence = Column(Text, nullable=True)  # Snippets/evidence from resume
    coverage_status = Column(String(50), default="uncovered", nullable=False)  # uncovered, partially_covered, covered

    session = relationship("InterviewSession", back_populates="competencies")
    questions = relationship("InterviewQuestion", back_populates="competency")
