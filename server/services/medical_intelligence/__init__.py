# =============================================================================
# services/medical_intelligence/__init__.py
# Enhanced with Scalable Specialty Architecture
# =============================================================================

import logging
from typing import Dict, List, Optional
from datetime import datetime

# Import core components
from .core import (
    ExternalMedicalAPIClient, 
    MedicalSpecialty,
    ConfidenceScorer,
    MedicationExtractionService,
    LearningManager,
    enhanced_medication_lookup,
    get_specialty_context_suggestions
)

# Import specialty management
from .specialties import specialty_registry, SpecialtyInterface

logger = logging.getLogger(__name__)

class MedicalIntelligenceService:
    """
    Enhanced Medical Intelligence Service with Scalable Specialty Architecture
    Routes requests to appropriate specialized services based on context
    """
    
    def __init__(self):
        # Initialize core services
        self.general_extraction = MedicationExtractionService()
        self.api_client = ExternalMedicalAPIClient()
        self.learning_manager = LearningManager()
        
        # Use specialty registry for routing
        self.specialty_registry = specialty_registry
        
        # Track available specialties
        self.available_specialties = ["general"] + self.specialty_registry.get_available_specialties()
        
    async def process_medical_text(self, text: str, session_id: str, 
                                 specialty: str = "general",
                                 patient_profile: Optional[Dict] = None) -> Dict:
        """
        Main entry point for medical text processing
        Routes to appropriate specialty service
        """
        
        logger.info(f"🧠 Processing medical text - specialty: {specialty}")
        
        # Auto-detect specialty if not specified or if general
        if specialty == "general":
            detected_specialty = self.specialty_registry.detect_specialty(text, patient_profile)
            if detected_specialty != "general":
                specialty = detected_specialty
                logger.info(f"🎯 Auto-detected specialty: {specialty}")
        
        # Route to appropriate service
        specialty_service = self.specialty_registry.get_specialty(specialty)
        
        if specialty_service:
            logger.info(f"🏥 Routing to {specialty} specialty service")
            return await specialty_service.process_text(text, session_id, patient_profile)
        else:
            logger.info(f"📋 Using general extraction for {specialty}")
            # Use general extraction for unknown/unsupported specialties
            return await self.general_extraction.extract_medications(
                text, session_id, specialty
            )
    
    async def get_medication_safety(self, medication_name: str, 
                                  specialty: str = "general",
                                  context: Optional[Dict] = None) -> Dict:
        """Get medication safety information for specific specialty"""
        
        specialty_service = self.specialty_registry.get_specialty(specialty)
        
        if specialty_service:
            return await specialty_service.get_medication_safety(medication_name, context)
        else:
            # Use general API lookup
            return await enhanced_medication_lookup(medication_name, specialty)
    
    async def record_feedback(self, extraction_id: str, feedback: Dict[str, bool],
                            feedback_type: str = "user") -> Dict:
        """Record feedback for learning system"""
        return await self.learning_manager.record_feedback(
            extraction_id, feedback, feedback_type
        )
    
    async def get_learning_analytics(self, specialty: str = "all", 
                                   time_period_days: int = 30) -> Dict:
        """Get learning analytics for specified specialty"""
        
        base_analytics = await self.learning_manager.get_learning_analytics(time_period_days)
        
        # Add specialty-specific metrics if needed
        if specialty != "all":
            base_analytics["specialty"] = specialty
            # Future: Add specialty-specific learning metrics filtering
        
        return base_analytics
    
    async def get_specialty_suggestions(self, text: str, specialty: str = "general") -> List[str]:
        """Get specialty-specific follow-up suggestions"""
        
        specialty_service = self.specialty_registry.get_specialty(specialty)
        
        if specialty_service and hasattr(specialty_service, 'get_suggestions'):
            # Future: implement get_suggestions in SpecialtyInterface
            return await specialty_service.get_suggestions(text)
        else:
            return await get_specialty_context_suggestions(text, specialty)
    
    def get_available_specialties(self) -> List[str]:
        """Get list of available medical specialties"""
        return self.available_specialties.copy()
    
    def register_specialty(self, specialty_class: type) -> bool:
        """Register a new medical specialty"""
        try:
            self.specialty_registry.register_specialty(specialty_class)
            self.available_specialties = ["general"] + self.specialty_registry.get_available_specialties()
            return True
        except Exception as e:
            logger.error(f"Failed to register specialty: {e}")
            return False

# =============================================================================
# Global service instance and convenience functions
# =============================================================================

# Global service instance
_medical_intelligence = MedicalIntelligenceService()

# Existing interface functions (maintained for backward compatibility)
async def extract_medications(text: str, session_id: str, medical_context: str = "general") -> Dict:
    """Extract medications using enhanced intelligence"""
    return await _medical_intelligence.process_medical_text(text, session_id, medical_context)

async def medication_lookup(drug_name: str, specialty: str = "general") -> Dict:
    """Lookup medication information"""
    return await _medical_intelligence.get_medication_safety(drug_name, specialty)

async def record_extraction_feedback(extraction_id: str, feedback: Dict[str, bool]) -> Dict:
    """Record feedback for learning"""
    return await _medical_intelligence.record_feedback(extraction_id, feedback)

async def get_analytics(specialty: str = "all", days: int = 30) -> Dict:
    """Get learning analytics"""
    return await _medical_intelligence.get_learning_analytics(specialty, days)

# Specialty-specific interface functions
async def process_specialty_case(text: str, session_id: str, specialty: str,
                                patient_profile: Optional[Dict] = None) -> Dict:
    """Process medical case for specific specialty"""
    return await _medical_intelligence.process_medical_text(text, session_id, specialty, patient_profile)

async def check_medication_safety(medication_name: str, specialty: str = "general", 
                                context: Optional[Dict] = None) -> Dict:
    """Check medication safety for specific specialty context"""
    return await _medical_intelligence.get_medication_safety(medication_name, specialty, context)

# OBGYN-specific convenience functions (for backward compatibility)
async def process_obgyn_case(text: str, session_id: str, patient_profile: Optional[Dict] = None) -> Dict:
    """Process OBGYN medical case"""
    return await _medical_intelligence.process_medical_text(text, session_id, "obgyn", patient_profile)

async def check_pregnancy_medication_safety(medication_name: str, gestational_weeks: int = 0) -> Dict:
    """Check medication safety during pregnancy"""
    if gestational_weeks <= 13:
        stage = "first_trimester"
    elif gestational_weeks <= 27:
        stage = "second_trimester"
    elif gestational_weeks > 0:
        stage = "third_trimester"
    else:
        stage = "not_pregnant"
    
    context = {"pregnancy_stage": stage, "gestational_weeks": gestational_weeks}
    return await _medical_intelligence.get_medication_safety(medication_name, "obgyn", context)

async def analyze_pregnancy_med_profile(medications: List[str], gestational_weeks: int) -> Dict:
    """Analyze complete medication profile for pregnant patient"""
    # Get OBGYN specialty service
    obgyn_service = _medical_intelligence.specialty_registry.get_specialty("obgyn")
    if obgyn_service:
        return await obgyn_service.intelligence.analyze_pregnancy_medication_profile(
            medications, gestational_weeks
        )
    else:
        return {"error": "OBGYN specialty not available"}

# Registry management functions
def register_new_specialty(specialty_class: type) -> bool:
    """Register a new medical specialty"""
    return _medical_intelligence.register_specialty(specialty_class)

def get_available_specialties() -> List[str]:
    """Get list of available medical specialties"""
    return _medical_intelligence.get_available_specialties()

# Health check function
async def health_check() -> Dict:
    """Health check for medical intelligence services"""
    try:
        # Test API connectivity
        api_status = await _medical_intelligence.api_client.test_api_connectivity()
        
        # Test specialty availability
        available_specialties = _medical_intelligence.get_available_specialties()
        
        # Test a specialty service if available
        specialty_status = {}
        for specialty in available_specialties:
            if specialty != "general":
                try:
                    specialty_service = _medical_intelligence.specialty_registry.get_specialty(specialty)
                    if specialty_service:
                        # Test with a simple medication lookup
                        test_result = await specialty_service.get_medication_safety("test_medication")
                        specialty_status[specialty] = "operational" if "error" not in test_result else "degraded"
                    else:
                        specialty_status[specialty] = "unavailable"
                except Exception as e:
                    specialty_status[specialty] = f"error: {str(e)}"
        
        return {
            "status": "healthy",
            "api_connectivity": api_status,
            "available_specialties": available_specialties,
            "specialty_status": specialty_status,
            "core_services": {
                "extraction": "operational",
                "learning": "operational",
                "confidence_scoring": "operational"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Export all public interfaces
__all__ = [
    # Core service class
    "MedicalIntelligenceService",
    
    # Main functions
    "extract_medications",
    "medication_lookup", 
    "record_extraction_feedback",
    "get_analytics",
    
    # Specialty functions
    "process_specialty_case",
    "check_medication_safety",
    
    # OBGYN convenience functions
    "process_obgyn_case",
    "check_pregnancy_medication_safety", 
    "analyze_pregnancy_med_profile",
    
    # Registry functions
    "register_new_specialty",
    "get_available_specialties",
    
    # Utility functions
    "health_check"
]