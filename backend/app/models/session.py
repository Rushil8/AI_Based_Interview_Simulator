import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid():
    return uuid.uuid4().hex


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    profile_id = Column(String(36), ForeignKey("candidate_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    
    job_role = Column(String(255), nullable=False)
    job_description = Column(Text, nullable=True)
    # Status: setup, in_progress, completed, abandoned
    status = Column(String(50), default="setup", nullable=False, index=True)
    
    # junior, mid, senior
    difficulty = Column(String(50), default="mid", nullable=False)
    duration_minutes = Column(Integer, default=30, nullable=False)
    target_question_count = Column(Integer, default=5, nullable=False)
    current_question_index = Column(Integer, default=0, nullable=False)
    
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions")
    profile = relationship("CandidateProfile", back_populates="sessions")
    competencies = relationship("Competency", back_populates="session", cascade="all, delete-orphan", order_by="Competency.importance_weight.desc()")
    questions = relationship("InterviewQuestion", back_populates="session", cascade="all, delete-orphan", order_by="InterviewQuestion.sequence_number.asc()")
    answers = relationship("CandidateAnswer", back_populates="session", cascade="all, delete-orphan")
    report = relationship("SessionReport", back_populates="session", uselist=False, cascade="all, delete-orphan")
