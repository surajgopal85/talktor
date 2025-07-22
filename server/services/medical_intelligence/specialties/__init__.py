# =============================================================================
# services/medical_intelligence/specialties/__init__.py
# =============================================================================

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
        try:
            # Access class attribute directly
            specialty_name = specialty_class.specialty_name
            self._specialties[specialty_name] = specialty_class
            logger.info(f"📋 Registered specialty: {specialty_name}")
            
            # DEBUG: Try to instantiate immediately to catch errors early
            test_instance = specialty_class()
            logger.info(f"✅ {specialty_name} specialty instantiated successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to register specialty {specialty_class}: {e}")
            import traceback
            logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            raise
    
    def get_specialty(self, specialty_name: str) -> Optional[SpecialtyInterface]:
        """Get initialized specialty instance with error handling"""
        try:
            if specialty_name not in self._initialized_specialties:
                if specialty_name in self._specialties:
                    logger.info(f"🔧 Initializing {specialty_name} specialty...")
                    self._initialized_specialties[specialty_name] = self._specialties[specialty_name]()
                    logger.info(f"✅ {specialty_name} specialty initialized successfully")
                else:
                    logger.warning(f"❌ Specialty '{specialty_name}' not found in registry")
                    logger.info(f"🔍 Available specialties: {list(self._specialties.keys())}")
                    return None
            
            return self._initialized_specialties[specialty_name]
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize {specialty_name} specialty: {e}")
            logger.error(f"🔍 Error details: {repr(e)}")
            return None
    
    def detect_specialty(self, text: str, patient_profile: Optional[Dict] = None) -> str:
        """Auto-detect specialty from text and patient profile"""
        text_lower = text.lower()
        
        # Check each registered specialty's keywords
        for specialty_name, specialty_class in self._specialties.items():
            try:
                # Access class attribute directly (not property)
                keywords = specialty_class.keywords
                if isinstance(keywords, list):
                    matched_keywords = [kw for kw in keywords if kw in text_lower]
                    if matched_keywords:
                        logger.info(f"🎯 Auto-detected specialty: {specialty_name} (matched: {matched_keywords[:3]}...)")
                        return specialty_name
            except Exception as e:
                logger.warning(f"⚠️ Error checking keywords for {specialty_name}: {e}")
        
        return "general"
    
    def get_available_specialties(self) -> List[str]:
        """Get list of available specialty names"""
        return list(self._specialties.keys())
    
    def debug_registry_status(self) -> Dict:
        """Debug method to check registry status"""
        status = {
            "registered_specialties": list(self._specialties.keys()),
            "initialized_specialties": list(self._initialized_specialties.keys()),
            "specialty_details": {}
        }
        
        for name, specialty_class in self._specialties.items():
            try:
                keywords = getattr(specialty_class, 'keywords', [])
                status["specialty_details"][name] = {
                    "class": str(specialty_class),
                    "keywords_count": len(keywords) if isinstance(keywords, list) else 0,
                    "sample_keywords": keywords[:5] if isinstance(keywords, list) else []
                }
            except Exception as e:
                status["specialty_details"][name] = {"error": str(e)}
        
        return status

# Global registry instance
specialty_registry = SpecialtyRegistry()

def _register_available_specialties():
    """Register all available specialties with comprehensive debugging"""
    logger.info("🔧 === STARTING SPECIALTY REGISTRATION ===")
    
    try:
        logger.info("🔧 Step 1: Testing OBGYN module imports...")
        
        # Test imports step by step
        try:
            from . import obgyn
            logger.info("✅ Step 1a: 'obgyn' module imported")
        except Exception as e:
            logger.error(f"❌ Step 1a FAILED: obgyn module - {e}")
            return
        
        try:
            from .obgyn import integration
            logger.info("✅ Step 1b: 'obgyn.integration' module imported")
        except Exception as e:
            logger.error(f"❌ Step 1b FAILED: obgyn.integration - {e}")
            return
        
        try:
            from .obgyn.integration import OBGYNSpecialty
            logger.info("✅ Step 1c: 'OBGYNSpecialty' class imported")
        except Exception as e:
            logger.error(f"❌ Step 1c FAILED: OBGYNSpecialty class - {e}")
            return
        
        logger.info("🔧 Step 2: Checking OBGYNSpecialty class...")
        
        # Check required attributes
        if not hasattr(OBGYNSpecialty, 'specialty_name'):
            logger.error("❌ Step 2 FAILED: OBGYNSpecialty missing 'specialty_name'")
            return
        
        if not hasattr(OBGYNSpecialty, 'keywords'):
            logger.error("❌ Step 2 FAILED: OBGYNSpecialty missing 'keywords'")
            return
        
        logger.info(f"✅ Step 2: specialty_name = '{OBGYNSpecialty.specialty_name}'")
        logger.info(f"✅ Step 2: keywords count = {len(OBGYNSpecialty.keywords)}")
        
        logger.info("🔧 Step 3: Adding Spanish keywords...")
        
        # Add Spanish keywords
        spanish_keywords = [
            "embarazada", "embarazo", "tomando", "vitaminas prenatales", 
            "ácido fólico", "anticonceptivos", "menstruación", "ginecólogo",
            "primer trimestre", "segundo trimestre", "tercer trimestre",
            "amamantando", "lactancia", "posparto", "medicamento", "medicina",
            "pastillas", "vitaminas", "tratamiento", "dosis", "síntomas"
        ]
        
        # Extend keywords
        original_keywords = list(OBGYNSpecialty.keywords)
        OBGYNSpecialty.keywords = original_keywords + spanish_keywords
        
        logger.info(f"✅ Step 3: Added {len(spanish_keywords)} Spanish keywords")
        logger.info(f"✅ Step 3: Total keywords now: {len(OBGYNSpecialty.keywords)}")
        
        logger.info("🔧 Step 4: Registering OBGYN specialty...")
        
        # Register the specialty
        specialty_registry.register_specialty(OBGYNSpecialty)
        logger.info(f"✅ Step 4: OBGYN specialty registered successfully")
        
        logger.info("🔧 Step 5: Testing specialty detection...")
        
        # Test detection
        test_cases = [
            "embarazada tomando vitaminas",
            "pregnant taking vitamins"
        ]
        
        for test_text in test_cases:
            detected = specialty_registry.detect_specialty(test_text)
            logger.info(f"🧪 '{test_text}' → '{detected}'")
        
        logger.info("🔧 Step 6: Testing specialty instantiation...")
        
        # Test instantiation
        obgyn_instance = specialty_registry.get_specialty("obgyn")
        if obgyn_instance:
            logger.info(f"✅ Step 6: OBGYN specialty instance created successfully")
        else:
            logger.error(f"❌ Step 6: Could not create OBGYN specialty instance")
        
        logger.info("🎉 === SPECIALTY REGISTRATION COMPLETE ===")
        
    except Exception as e:
        logger.error(f"❌ SPECIALTY REGISTRATION FAILED: {e}")
        import traceback
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")

# Register specialties on module import
_register_available_specialties()

def debug_specialty_system():
    """Debug function to check entire specialty system"""
    logger.info("🔍 === SPECIALTY SYSTEM DEBUG ===")
    
    # Check registry status
    status = specialty_registry.debug_registry_status()
    logger.info(f"📊 Registry status: {status}")
    
    return status

# Export everything
__all__ = [
    "SpecialtyInterface",
    "SpecialtyRegistry", 
    "specialty_registry",
    "debug_specialty_system"
]