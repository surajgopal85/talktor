# services/ml/simple_bert_context.py
# Simple approach that trusts BERT's contextual understanding

import logging
from typing import Dict, List
from .medical_bert import MedicalSpanishBERT

logger = logging.getLogger(__name__)

class SimpleBERTContextAnalyzer:
    """
    Simple context analyzer that trusts BERT's built-in contextual understanding
    No hardcoded rules - let BERT do what it was trained to do
    """
    
    def __init__(self):
        self.bert = MedicalSpanishBERT()
    
    async def is_medical_context(self, text: str) -> Dict:
        """
        Simple medical context detection using BERT
        """
        # Let BERT analyze the text
        bert_result = await self.bert.extract_medical_entities(text)
        
        # Simple heuristics based on BERT's output
        medical_entities_found = len(bert_result.entities)
        medical_confidence = bert_result.bert_confidence
        
        # BERT found medical entities = medical context
        is_medical = medical_entities_found > 0 and medical_confidence > 0.5
        
        return {
            "is_medical_context": is_medical,
            "confidence": medical_confidence,
            "medical_entities_count": medical_entities_found,
            "reasoning": "bert_detected_medical_entities" if is_medical else "no_medical_entities_detected"
        }
    
    async def get_translation_context_hint(self, spanish_text: str) -> Dict:
        """
        Get translation context hint from BERT (not hardcoded rules)
        """
        # Analyze with BERT
        context_analysis = await self.is_medical_context(spanish_text)
        
        # Simple decision based on BERT's analysis
        if context_analysis["is_medical_context"]:
            return {
                "suggested_context": "medical",
                "confidence": context_analysis["confidence"],
                "reasoning": "BERT detected medical entities in text"
            }
        else:
            return {
                "suggested_context": "general", 
                "confidence": 1.0 - context_analysis["confidence"],
                "reasoning": "No medical entities detected by BERT"
            }

class MinimalTranslationEnhancer:
    """
    Minimal translation enhancer that uses BERT context without hardcoded rules
    """
    
    def __init__(self):
        self.context_analyzer = SimpleBERTContextAnalyzer()
        
        # Only store the most critical medical translation mappings
        self.critical_medical_translations = {
            # Only the most important and unambiguous cases
            "medical_context": {
                "tomar": "take",
                "tomo": "take", 
                "tomando": "taking"
            },
            "general_context": {
                "tomar": "drink",
                "tomo": "drink",
                "tomando": "drinking"  
            }
        }
    
    async def enhance_translation(self, spanish_text: str, base_translation: str) -> Dict:
        """
        Enhance translation using BERT context (minimal approach)
        """
        # Get context hint from BERT
        context_hint = await self.context_analyzer.get_translation_context_hint(spanish_text)
        
        enhanced_translation = base_translation
        corrections_applied = []
        
        # Only apply corrections for high-confidence medical context
        if (context_hint["suggested_context"] == "medical" and 
            context_hint["confidence"] > 0.7):
            
            # Apply minimal critical corrections
            for spanish_word, medical_translation in self.critical_medical_translations["medical_context"].items():
                general_translation = self.critical_medical_translations["general_context"][spanish_word]
                
                if spanish_word in spanish_text.lower() and general_translation in base_translation.lower():
                    enhanced_translation = enhanced_translation.replace(
                        general_translation, medical_translation
                    )
                    corrections_applied.append({
                        "word": spanish_word,
                        "from": general_translation,
                        "to": medical_translation
                    })
        
        return {
            "enhanced_translation": enhanced_translation,
            "corrections_applied": corrections_applied,
            "bert_context_detected": context_hint["suggested_context"],
            "bert_confidence": context_hint["confidence"]
        }

# Even simpler approach - just boost existing extractions when BERT agrees
class BERTConfidenceBooster:
    """
    Simplest possible approach: just boost confidence when BERT agrees
    """
    
    def __init__(self):
        self.bert = MedicalSpanishBERT()
    
    async def boost_extraction_confidence(self, medications: List[Dict], original_text: str) -> List[Dict]:
        """
        Boost confidence for medications that BERT also detected
        """
        # Get BERT's analysis
        bert_result = await self.bert.extract_medical_entities(original_text)
        bert_medication_terms = {
            entity.spanish_term.lower() 
            for entity in bert_result.entities 
            if entity.entity_type == "medication"
        }
        
        # Boost confidence for medications BERT also found
        boosted_medications = []
        for med in medications:
            med_copy = med.copy()
            original_term = med["original_term"].lower()
            
            # If BERT also detected this as a medication, boost confidence
            if any(bert_term in original_term or original_term in bert_term 
                   for bert_term in bert_medication_terms):
                
                original_confidence = med_copy["extraction_confidence"]
                boost = min(0.2, 1.0 - original_confidence)  # Up to 0.2 boost, cap at 1.0
                med_copy["extraction_confidence"] = original_confidence + boost
                med_copy["bert_confidence_boost"] = boost
                med_copy["bert_agreement"] = True
            else:
                med_copy["bert_confidence_boost"] = 0.0
                med_copy["bert_agreement"] = False
            
            boosted_medications.append(med_copy)
        
        return boosted_medications

# Integration example - much simpler
class SimpleEnhancedExtraction:
    """
    Simple integration that just boosts confidence when BERT agrees
    """
    
    def __init__(self, base_extraction_service):
        self.base_service = base_extraction_service
        self.confidence_booster = BERTConfidenceBooster()
    
    async def extract_medications(self, text: str, session_id: str, medical_context: str = "general"):
        """
        Simple enhancement: run base extraction, then boost confidence where BERT agrees
        """
        # Run your existing extraction
        base_result = await self.base_service.extract_medications(text, session_id, medical_context)
        
        try:
            # Boost confidence using BERT
            enhanced_medications = await self.confidence_booster.boost_extraction_confidence(
                base_result["medications"], text
            )
            base_result["medications"] = enhanced_medications
            base_result["bert_enhanced"] = True
            
        except Exception as e:
            logger.warning(f"BERT enhancement failed, using base result: {e}")
            base_result["bert_enhanced"] = False
        
        return base_result