# models/database/__init__.py

"""
Database Models Package

SQLAlchemy models for Talktor medical interpreter:
- Session management and user interactions
- Speech-to-text transcription records  
- Medical translation with context
- Medication extraction and learning data
- Feedback collection for reinforcement learning
- Analytics and performance metrics
"""

from .base import Base, engine, SessionLocal, get_db
from .models import (
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