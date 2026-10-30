import uuid
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid():
    return uuid.uuid4().hex


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    session_id = Column(String(36), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    competency_id = Column(String(36), ForeignKey("competencies.id", ondelete="SET NULL"), nullable=True, index=True)

    sequence_number = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default="technical", nullable=False)  # technical, scenario, project, problem_solving, behavioral
    difficulty = Column(String(50), default="mid", nullable=False)  # junior, mid, senior
    
    # Stored as JSON strings
    expected_elements_json = Column(Text, nullable=False)
    rubric_json = Column(Text, nullable=False)
    
    maximum_score = Column(Float, default=100.0, nullable=False)
    follow_up_guidance = Column(Text, nullable=True)
    is_adaptive_followup = Column(Boolean, default=False, nullable=False)
    adaptation_reason = Column(Text, nullable=True)

    session = relationship("InterviewSession", back_populates="questions")
    competency = relationship("Competency", back_populates="questions")
    answers = relationship("CandidateAnswer", back_populates="question", cascade="all, delete-orphan")
