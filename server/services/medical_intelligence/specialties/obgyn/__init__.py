# =============================================================================
# services/medical_intelligence/specialties/obgyn/__init__.py
# =============================================================================

"""
OBGYN (Obstetrics and Gynecology) Medical Specialty Module
Provides comprehensive women's health medical intelligence
"""

from .specialty_engine import OBGYNSpecialtyEngine, PregnancyStage, OBGYNCondition
from .extraction import OBGYNEnhancedExtractionService
from .integration import OBGYNMedicalIntelligence, OBGYNSpecialty

# Convenience functions
from .integration import (
    process_obgyn_medical_text,
    get_obgyn_medication_safety,
    analyze_pregnancy_medications
)

__all__ = [
    # Core classes
    "OBGYNSpecialtyEngine",
    "OBGYNEnhancedExtractionService", 
    "OBGYNMedicalIntelligence",
    "OBGYNSpecialty",
    
    # Enums
    "PregnancyStage",
    "OBGYNCondition",
    
    # Functions
    "process_obgyn_medical_text",
    "get_obgyn_medication_safety", 
    "analyze_pregnancy_medications"
]