# =============================================================================
# services/medical_intelligence/specialties/__init__.py
# =============================================================================

"""
Medical specialties module - organizes specialty-specific intelligence
"""

import logging
from typing import Dict, List, Optional, Type
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class SpecialtyInterface(ABC):
    """Base interface for all medical specialties"""
    
    # Class attributes that must be defined by subclasses
    specialty_name: str
    keywords: List[str]
    
    @abstractmethod
    async def process_text(self, text: str, session_id: str, 
                          patient_profile: Optional[Dict] = None) -> Dict:
        """Process text for this specialty"""
        pass
    
    @abstractmethod
    async def get_medication_safety(self, medication_name: str, 
                                  context: Optional[Dict] = None) -> Dict:
        """Get medication safety for this specialty"""
        pass

class SpecialtyRegistry:
    """Registry for managing available medical specialties"""
    
    def __init__(self):
        self._specialties: Dict[str, Type[SpecialtyInterface]] = {}
        self._initialized_specialties: Dict[str, SpecialtyInterface] = {}
    
    def register_specialty(self, specialty_class: Type[SpecialtyInterface]):
        """Register a specialty class"""
        # Access class attribute directly
        specialty_name = specialty_class.specialty_name
        self._specialties[specialty_name] = specialty_class
        logger.info(f"📋 Registered specialty: {specialty_name}")
    
    def get_specialty(self, specialty_name: str) -> Optional[SpecialtyInterface]:
        """Get initialized specialty instance"""
        if specialty_name not in self._initialized_specialties:
            if specialty_name in self._specialties:
                self._initialized_specialties[specialty_name] = self._specialties[specialty_name]()
            else:
                return None
        
        return self._initialized_specialties[specialty_name]
    
    def detect_specialty(self, text: str, patient_profile: Optional[Dict] = None) -> str:
        """Auto-detect specialty from text and patient profile"""
        text_lower = text.lower()
        
        # Check each registered specialty's keywords
        for specialty_name, specialty_class in self._specialties.items():
            # Access class attribute directly (not property)
            keywords = specialty_class.keywords
            if isinstance(keywords, list) and any(keyword in text_lower for keyword in keywords):
                logger.info(f"🎯 Auto-detected specialty: {specialty_name}")
                return specialty_name
        
        # Check patient profile
        if patient_profile:
            # OBGYN profile indicators
            if (patient_profile.get("pregnancy_status") or 
                patient_profile.get("gender") == "female"):
                conditions = str(patient_profile.get("conditions", [])).lower()
                if any(condition in conditions for condition in ["pregnancy", "pcos", "endometriosis"]):
                    return "obgyn"
        
        return "general"
    
    def get_available_specialties(self) -> List[str]:
        """Get list of available specialty names"""
        return list(self._specialties.keys())

# Global registry instance
specialty_registry = SpecialtyRegistry()

# Import and register specialties
def _register_available_specialties():
    """Register all available specialties"""
    try:
        from .obgyn.integration import OBGYNSpecialty
        specialty_registry.register_specialty(OBGYNSpecialty)
        logger.info(f"✅ Successfully registered OBGYN specialty")
    except ImportError as e:
        logger.warning(f"Failed to import OBGYN specialty: {e}")
    except Exception as e:
        logger.error(f"Failed to register OBGYN specialty: {e}")

# Register specialties on module import
_register_available_specialties()

# Future specialties would be imported here:
# from .cardiology import CardiologySpecialty
# specialty_registry.register_specialty(CardiologySpecialty)

__all__ = [
    "SpecialtyInterface",
    "SpecialtyRegistry", 
    "specialty_registry"
]