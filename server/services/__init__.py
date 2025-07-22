# =============================================================================
# services/__init__.py
# =============================================================================

"""
Talktor Services Package

Organized medical AI services following scalable architecture:
- medical_intelligence/: AI extraction, API clients, learning components
- translation/: Translation logic and medical-specific translation
- audio/: Speech processing (STT/TTS)
- session/: Session management and storage
"""

from .medical_intelligence.extraction import MedicationExtractionService
from .translation.translator import TranslationService
from .session.manager import SessionService
from .audio.whisper_service import WhisperService

__all__ = [
    "MedicationExtractionService",
    "TranslationService", 
    "SessionService",
    "WhisperService"
]