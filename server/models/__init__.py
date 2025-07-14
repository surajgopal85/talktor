# models/__init__.py

"""
Talktor Models Package

Data models and database schemas:
- Database models with SQLAlchemy
- Pydantic models for API validation
- Domain models for business logic
"""

# Import database models for easy access
from .database import (
    Base,
    engine,
    SessionLocal, 
    get_db,
    Session,
    Transcription,
    Translation,
    ExtractionAttempt,
    ExtractionCandidate,
    ExtractedMedication,
    ExtractionFeedback,
    LearningMetrics
)

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db", 
    "Session",
    "Transcription",
    "Translation",
    "ExtractionAttempt",
    "ExtractionCandidate", 
    "ExtractedMedication",
    "ExtractionFeedback",
    "LearningMetrics"
]