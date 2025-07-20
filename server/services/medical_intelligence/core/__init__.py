# =============================================================================
# services/medical_intelligence/core/__init__.py
# =============================================================================

"""
Core medical intelligence functionality shared across all specialties
"""

from .api_client import (
    ExternalMedicalAPIClient, 
    MedicalSpecialty,
    enhanced_medication_lookup, 
    get_specialty_context_suggestions
)
from .confidence import ConfidenceScorer
from .extraction import MedicationExtractionService
from .learning import LearningManager

__all__ = [
    "ExternalMedicalAPIClient",
    "MedicalSpecialty", 
    "ConfidenceScorer",
    "MedicationExtractionService",
    "LearningManager",
    "enhanced_medication_lookup",
    "get_specialty_context_suggestions"
]