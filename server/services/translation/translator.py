# =============================================================================
# services/translation/translator.py - FIXED IMPORT PATH
# =============================================================================

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class TranslationService:
    """Core translation service with medical context awareness"""
    
    def __init__(self):
        self.medical_enhancer = None
        # Spanish medical terms that need special handling
        self.spanish_medical_terms = {
            "tomando": "taking",  # NOT "drinking"
            "embarazada": "pregnant",
            "embarazo": "pregnancy", 
            "medicamento": "medication",
            "medicina": "medicine",
            "pastillas": "pills",
            "vitaminas": "vitamins",
            "ácido fólico": "folic acid",
            "vitaminas prenatales": "prenatal vitamins",
            "anticonceptivos": "birth control",
            "medicinas": "medicines",
            "tratamiento": "treatment",
            "dosis": "dose",
            "síntomas": "symptoms",
            "efectos secundarios": "side effects"
        }
    
    async def translate_with_medical_context(self, text: str, source_lang: str, 
                                           target_lang: str, medications: List[Dict]) -> Dict:
        """Translate text with medical context awareness"""
        try:
            from deep_translator import GoogleTranslator
            
            # PRE-PROCESS: Fix Spanish medical terms before translation
            if source_lang in ["es", "auto"] and "tomando" in text.lower():
                # Replace "tomando" with medical context
                text = self._fix_spanish_medical_context(text)
            
            # Standard translation
            if source_lang == "auto":
                translator = GoogleTranslator(source='auto', target=target_lang)
            else:
                translator = GoogleTranslator(source=source_lang, target=target_lang)
            
            standard_translation = translator.translate(text)
            
            # Enhanced translation with medical context
            enhanced_translation = await self._enhance_with_medical_context(
                standard_translation, medications, target_lang, source_lang
            )
            
            return {
                "standard_translation": standard_translation,
                "enhanced_translation": enhanced_translation,
                "medical_context_applied": True
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Translation failed: {e}")
            return {
                "standard_translation": f"[TRANSLATION FAILED] {text}",
                "enhanced_translation": f"[TRANSLATION FAILED] {text}",
                "medical_context_applied": False
            }
    
    def _fix_spanish_medical_context(self, text: str) -> str:
        """Fix Spanish medical terms for better translation"""
        fixed_text = text
        
        # Handle "tomando" in medical context
        if "tomando" in text.lower():
            # Look for medication context indicators
            medication_indicators = [
                "medicamento", "medicina", "pastillas", "vitaminas", 
                "mg", "gramos", "dosis", "píldora", "tableta"
            ]
            
            if any(indicator in text.lower() for indicator in medication_indicators):
                # Replace "tomando" with "taking" context
                fixed_text = fixed_text.replace("tomando", "tomando (taking medication)")
                fixed_text = fixed_text.replace("Tomando", "Tomando (taking medication)")
        
        return fixed_text
    
    async def _enhance_with_medical_context(self, translation: str, medications: List[Dict],
                                          target_lang: str, source_lang: str = None) -> str:
        """Enhance translation with medical context"""
        enhanced = translation
        
        # Post-process common medical translation errors
        if source_lang == "es" and target_lang == "en":
            # Fix common Spanish->English medical mistranslations
            enhanced = enhanced.replace("drinking", "taking")  # tomando fix
            enhanced = enhanced.replace("Drinking", "Taking")
            
            # Ensure pregnancy terms are correct
            if "embarazada" in translation.lower():
                enhanced = enhanced.replace("embarrassed", "pregnant")
                enhanced = enhanced.replace("Embarrassed", "Pregnant")
        
        return enhanced
    
    async def get_follow_up_questions(self, text: str, medical_context: str) -> List[str]:
        """Generate contextual follow-up questions"""
        try:
            # FIXED IMPORT PATH - moved to core
            from ..medical_intelligence.core.api_client import get_specialty_context_suggestions
            
            questions = await get_specialty_context_suggestions(text, medical_context)
            return questions
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to get follow-up questions: {e}")
            # Return fallback questions based on detected language
            if self._detect_spanish_content(text):
                return self._get_spanish_fallback_questions()
            
            return [
                "How long have you been experiencing these symptoms?",
                "Are you taking any other medications?", 
                "Do you have any known allergies?",
                "When was your last doctor visit?"
            ]
    
    def _detect_spanish_content(self, text: str) -> bool:
        """Detect if text contains Spanish content"""
        spanish_indicators = [
            "embarazada", "tomando", "medicamento", "síntomas", 
            "doctor", "medicina", "tratamiento", "dosis"
        ]
        return any(word in text.lower() for word in spanish_indicators)
    
    def _get_spanish_fallback_questions(self) -> List[str]:
        """Spanish-specific fallback questions"""
        return [
            "¿Cuánto tiempo ha tenido estos síntomas?",
            "¿Está tomando otros medicamentos?",
            "¿Tiene alguna alergia conocida?", 
            "¿Cuándo fue su última visita al médico?"
        ]

# # services/translation/translator.py - Fixed imports

# import logging
# from typing import Dict, List, Optional

# logger = logging.getLogger(__name__)

# class TranslationService:
#     """Core translation service with medical context awareness"""
    
#     def __init__(self):
#         self.medical_enhancer = None
        
#     async def translate_with_medical_context(self, text: str, source_lang: str, 
#                                            target_lang: str, medications: List[Dict]) -> Dict:
#         """Translate text with medical context awareness"""
        
#         try:
#             from deep_translator import GoogleTranslator
            
#             # Standard translation
#             if source_lang == "auto":
#                 translator = GoogleTranslator(source='auto', target=target_lang)
#             else:
#                 translator = GoogleTranslator(source=source_lang, target=target_lang)
            
#             standard_translation = translator.translate(text)
            
#             # Enhanced translation (future: medical-specific improvements)
#             enhanced_translation = await self._enhance_with_medical_context(
#                 standard_translation, medications, target_lang
#             )
            
#             return {
#                 "standard_translation": standard_translation,
#                 "enhanced_translation": enhanced_translation
#             }
            
#         except Exception as e:
#             logger.warning(f"⚠️ Translation failed: {e}")
#             return {
#                 "standard_translation": f"[TRANSLATION FAILED] {text}",
#                 "enhanced_translation": f"[TRANSLATION FAILED] {text}"
#             }
    
#     async def _enhance_with_medical_context(self, translation: str, medications: List[Dict], 
#                                           target_lang: str) -> str:
#         """Enhance translation with medical context (future ML enhancement)"""
#         # For now, return standard translation
#         # Future: Add medical term corrections, dosage translations, etc.
#         return translation
    
#     async def get_follow_up_questions(self, text: str, medical_context: str) -> List[str]:
#         """Generate contextual follow-up questions"""
        
#         try:
#             # Import from the correct location
#             from ..medical_intelligence.api_client import get_specialty_context_suggestions
#             questions = await get_specialty_context_suggestions(text, medical_context)
#             return questions
#         except Exception as e:
#             logger.warning(f"⚠️ Failed to get follow-up questions: {e}")
#             # Return fallback questions
#             return [
#                 "How long have you been experiencing these symptoms?",
#                 "Are you taking any other medications?", 
#                 "Do you have any known allergies?",
#                 "When was your last doctor visit?"
#             ]