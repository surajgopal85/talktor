# =============================================================================
# services/medical_intelligence/specialties/obgyn/__init__.py
# =============================================================================

"""
OBGYN (Obstetrics and Gynecology) Medical Specialty Module
Provides comprehensive women's health medical intelligence
"""

import logging

logger = logging.getLogger(__name__)

try:
    # Import core components
    from .specialty_engine import OBGYNSpecialtyEngine, PregnancyStage, OBGYNCondition
    logger.info("✅ OBGYN: specialty_engine imported")
    
    from .extraction import OBGYNEnhancedExtractionService
    logger.info("✅ OBGYN: extraction imported")
    
    from .integration import OBGYNMedicalIntelligence, OBGYNSpecialty
    logger.info("✅ OBGYN: integration imported")
    
    # Convenience functions
    from .integration import (
        process_obgyn_medical_text,
        get_obgyn_medication_safety,
        analyze_pregnancy_medications
    )
    logger.info("✅ OBGYN: convenience functions imported")
    
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
    
    logger.info("✅ OBGYN module initialization complete")
    
except ImportError as e:
    logger.error(f"❌ OBGYN module import failed: {e}")
    raise
except Exception as e:
    logger.error(f"❌ OBGYN module initialization failed: {e}")
    raise