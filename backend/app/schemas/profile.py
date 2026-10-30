from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class SkillEvidence(BaseModel):
    skill: str
    category: str = "technical"
    snippet: Optional[str] = None
    confidence: float = 1.0


class ProjectItem(BaseModel):
    title: str
    description: str
    technologies: List[str] = Field(default_factory=list)
    role: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    degree: str
    institution: str
    year: Optional[str] = None
    details: Optional[str] = None


class ExperienceItem(BaseModel):
    role: str
    company: str
    duration: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)


class StructuredProfile(BaseModel):
    full_name: Optional[str] = "Candidate"
    email: Optional[str] = None
    phone: Optional[str] = None
    summary: Optional[str] = None
    technical_skills: List[str] = Field(default_factory=list)
    programming_languages: List[str] = Field(default_factory=list)
    frameworks_libraries: List[str] = Field(default_factory=list)
    tools_platforms: List[str] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    work_experience: List[ExperienceItem] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    years_of_experience: float = 0.0
    evidence_map: Dict[str, str] = Field(default_factory=dict)


class CandidateProfileUpdate(BaseModel):
    structured_profile: StructuredProfile


class CandidateProfileResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    resume_filename: Optional[str] = None
    structured_profile: StructuredProfile
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
