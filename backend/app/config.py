import os
from typing import List
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI Interview Coach"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    # Defaults to SQLite for immediate local execution; configure PostgreSQL in .env
    DATABASE_URL: str = "sqlite:///./interview_coach.db"

    # AI Configuration (Gemini)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    MOCK_AI: bool = True  # Automatically set to False if valid GEMINI_API_KEY provided unless explicitly set

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production-ai-interview-coach-2026"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = [".pdf"]

    # Evaluation Rubric Weights (must total 1.0 / 100%)
    RUBRIC_WEIGHT_RELEVANCE: float = 0.20
    RUBRIC_WEIGHT_TECHNICAL: float = 0.40
    RUBRIC_WEIGHT_COMPLETENESS: float = 0.25
    RUBRIC_WEIGHT_COMMUNICATION: float = 0.15
    RUBRIC_VERSION: str = "v1.0"

    # Semantic Relevance Diagnostic Threshold (Sentence-BERT cosine similarity)
    SEMANTIC_SIMILARITY_FLAG_THRESHOLD: float = 0.50

    # Adaptive Controller Config
    MAX_CONSECUTIVE_LOW_SCORES: int = 2
    HIGH_SCORE_THRESHOLD: float = 80.0
    LOW_SCORE_THRESHOLD: float = 55.0
    DEFAULT_QUESTIONS_COUNT: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_weights_and_ai(self) -> "Settings":
        total_weight = (
            self.RUBRIC_WEIGHT_RELEVANCE
            + self.RUBRIC_WEIGHT_TECHNICAL
            + self.RUBRIC_WEIGHT_COMPLETENESS
            + self.RUBRIC_WEIGHT_COMMUNICATION
        )
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(
                f"Rubric weights must sum to 1.0 (100%). Current sum: {total_weight:.3f} "
                f"(Relevance: {self.RUBRIC_WEIGHT_RELEVANCE}, Technical: {self.RUBRIC_WEIGHT_TECHNICAL}, "
                f"Completeness: {self.RUBRIC_WEIGHT_COMPLETENESS}, Communication: {self.RUBRIC_WEIGHT_COMMUNICATION})"
            )

        # If GEMINI_API_KEY is provided and MOCK_AI wasn't explicitly forced to true in env, enable live AI
        if self.GEMINI_API_KEY and self.GEMINI_API_KEY.strip() and "MOCK_AI" not in os.environ:
            self.MOCK_AI = False

        return self


settings = Settings()
