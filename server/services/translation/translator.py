# =============================================================================
# services/translation/translator.py
# =============================================================================

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class TranslationService:
    """Core translation service with medical context awareness"""
    
    def __init__(self):
        self.medical_enhancer = None
        
    async def translate_with_medical_context(self, text: str, source_lang: str, 
                                           target_lang: str, medications: List[Dict]) -> Dict:
        """Translate text with medical context awareness"""
        
        try:
            from deep_translator import GoogleTranslator
            
            # Standard translation
            if source_lang == "auto":
                translator = GoogleTranslator(source='auto', target=target_lang)
            else:
                translator = GoogleTranslator(source=source_lang, target=target_lang)
            
            standard_translation = translator.translate(text)
            
            # Enhanced translation (future: medical-specific improvements)
            enhanced_translation = await self._enhance_with_medical_context(
                standard_translation, medications, target_lang
            )
            
            return {
                "standard_translation": standard_translation,
                "enhanced_translation": enhanced_translation
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Translation failed: {e}")
            return {
                "standard_translation": f"[TRANSLATION FAILED] {text}",
                "enhanced_translation": f"[TRANSLATION FAILED] {text}"
            }
    
    async def _enhance_with_medical_context(self, translation: str, medications: List[Dict], 
                                          target_lang: str) -> str:
        """Enhance translation with medical context (future ML enhancement)"""
        # For now, return standard translation
        # Future: Add medical term corrections, dosage translations, etc.
        return translation
    
    async def get_follow_up_questions(self, text: str, medical_context: str) -> List[str]:
        """Generate contextual follow-up questions"""
        
        try:
            from external_medical_intelligence import get_specialty_context_suggestions
            questions = await get_specialty_context_suggestions(text, medical_context)
            return questions
        except Exception as e:
            logger.warning(f"⚠️ Failed to get follow-up questions: {e}")
            return [
                "How long have you been experiencing these symptoms?",
                "Are you taking any other medications?", 
                "Do you have any known allergies?"
            ]