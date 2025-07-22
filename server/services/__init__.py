# =============================================================================
# services/__init__.py
# Updated for new scalable architecture
# =============================================================================
"""
Talktor Services Package
Organized medical AI services following scalable architecture:
- medical_intelligence/: AI extraction, API clients, learning components (now with specialties)
- translation/: Translation logic and medical-specific translation
- audio/: Speech processing (STT/TTS)  
- session/: Session management and storage
"""

# Updated imports for new architecture
from .medical_intelligence import MedicationExtractionService, LearningManager
from .translation.translator import TranslationService
from .session.manager import SessionService
from .audio.whisper_service import WhisperService

__all__ = [
    "MedicationExtractionService",
    "LearningManager", 
    "TranslationService",
    "SessionService", 
    "WhisperService"
]