# models/database/models.py

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import uuid

class Session(Base):
    """User sessions for tracking interactions"""
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), onupdate=func.now())
    user_language = Column(String(10))  # Source language
    target_language = Column(String(10))  # Target language
    medical_context = Column(String(50))  # general, obgyn, cardiology, etc.
    
    # Relationships
    transcriptions = relationship("Transcription", back_populates="session", cascade="all, delete-orphan")
    translations = relationship("Translation", back_populates="session", cascade="all, delete-orphan")
    extractions = relationship("ExtractionAttempt", back_populates="session", cascade="all, delete-orphan")

class Transcription(Base):
    """Speech-to-text transcription records"""
    __tablename__ = "transcriptions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Transcription data
    text = Column(Text, nullable=False)
    language_detected = Column(String(10))
    confidence = Column(Float)
    audio_duration = Column(Float)  # Duration in seconds
    
    # Relationship
    session = relationship("Session", back_populates="transcriptions")

class Translation(Base):
    """Translation records with medical context"""
    __tablename__ = "translations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Translation data
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)
    enhanced_translation = Column(Text)  # Future: medical-enhanced translation
    source_language = Column(String(10))
    target_language = Column(String(10))
    
    # Medical context
    medical_context = Column(String(50))
    medical_accuracy_score = Column(Float)
    follow_up_questions = Column(JSON)  # Array of questions
    
    # Relationship
    session = relationship("Session", back_populates="translations")

class ExtractionAttempt(Base):
    """Medication extraction attempts for learning"""
    __tablename__ = "extraction_attempts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Extraction input
    original_text = Column(Text, nullable=False)
    medical_context = Column(String(50))
    
    # Extraction process data
    total_candidates = Column(Integer)
    successful_extractions = Column(Integer)
    extraction_strategies_used = Column(JSON)  # Array of strategy names
    confidence_threshold_used = Column(Float)
    
    # Learning status
    learning_status = Column(String(50), default="pending_feedback")  # pending_feedback, feedback_received, training_data
    feedback_timestamp = Column(DateTime(timezone=True))
    
    # Relationships
    session = relationship("Session", back_populates="extractions")
    candidates = relationship("ExtractionCandidate", back_populates="extraction", cascade="all, delete-orphan")
    medications = relationship("ExtractedMedication", back_populates="extraction", cascade="all, delete-orphan")
    feedback_items = relationship("ExtractionFeedback", back_populates="extraction", cascade="all, delete-orphan")

class ExtractionCandidate(Base):
    """Individual candidates identified during extraction"""
    __tablename__ = "extraction_candidates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    extraction_id = Column(String, ForeignKey("extraction_attempts.id"), nullable=False)
    
    # Candidate data
    term = Column(String(255), nullable=False)
    strategy = Column(String(50))  # single_word, bigram, pattern_match
    context = Column(Text)  # Surrounding words
    position = Column(Integer)  # Position in original text
    confidence_modifiers = Column(JSON)  # Strategy-specific data
    
    # Relationship
    extraction = relationship("ExtractionAttempt", back_populates="candidates")

class ExtractedMedication(Base):
    """Successfully extracted and validated medications"""
    __tablename__ = "extracted_medications"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    extraction_id = Column(String, ForeignKey("extraction_attempts.id"), nullable=False)
    
    # Medication identification
    original_term = Column(String(255), nullable=False)
    canonical_name = Column(String(255))
    rxcui = Column(String(50))  # RxNorm identifier
    
    # Extraction metadata
    extraction_confidence = Column(Float)
    extraction_strategy = Column(String(50))
    context = Column(Text)
    position = Column(Integer)
    
    # API data (cached for performance)
    api_data = Column(JSON)  # Full API response for rich context
    brand_names = Column(JSON)  # Array of brand names
    indications = Column(JSON)  # Array of medical uses
    contraindications = Column(JSON)  # Array of contraindications
    pregnancy_category = Column(String(10))
    
    # Validation timestamp
    validated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    extraction = relationship("ExtractionAttempt", back_populates="medications")

class ExtractionFeedback(Base):
    """Doctor/user feedback on extraction accuracy"""
    __tablename__ = "extraction_feedback"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    extraction_id = Column(String, ForeignKey("extraction_attempts.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Feedback data
    medication_term = Column(String(255), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    feedback_type = Column(String(50))  # doctor, patient, automated
    confidence_in_feedback = Column(Float)  # How sure is the feedback provider
    
    # Additional context
    notes = Column(Text)  # Optional feedback notes
    suggested_correction = Column(String(255))  # If incorrect, what should it be
    
    # Relationship
    extraction = relationship("ExtractionAttempt", back_populates="feedback_items")

class LearningMetrics(Base):
    """Aggregated learning metrics for analytics"""
    __tablename__ = "learning_metrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Time period for metrics
    period_start = Column(DateTime(timezone=True))
    period_end = Column(DateTime(timezone=True))
    
    # Extraction metrics
    total_extractions = Column(Integer)
    extractions_with_feedback = Column(Integer)
    average_confidence = Column(Float)
    accuracy_rate = Column(Float)
    
    # Strategy performance
    strategy_performance = Column(JSON)  # Performance by extraction strategy
    
    # Learning readiness
    ready_for_training = Column(Boolean)
    training_data_size = Column(Integer)