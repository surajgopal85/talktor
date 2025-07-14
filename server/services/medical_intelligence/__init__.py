# =============================================================================
# services/medical_intelligence/__init__.py
# =============================================================================


"""
Medical Intelligence Services

AI-powered medical analysis including:
- Medication extraction with multiple strategies
- External API integration (RxNorm, FDA)
- Confidence scoring and learning components
- RL infrastructure for continuous improvement
"""

from .extraction import MedicationExtractionService
from .api_client import ExternalMedicalAPIClient
from .confidence import ConfidenceScorer
from .learning import LearningManager

__all__ = [
    "MedicationExtractionService",
    "ExternalMedicalAPIClient", 
    "ConfidenceScorer",
    "LearningManager"
]