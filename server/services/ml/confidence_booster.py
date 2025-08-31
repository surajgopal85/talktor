# services/ml/confidence_booster.py
# Memory-optimized BERT confidence enhancement for existing extraction results

import logging
from typing import Dict, List
from .medical_bert import MedicalSpanishBERT

logger = logging.getLogger(__name__)

class BERTConfidenceBooster:
    """
    Memory-optimized confidence booster using singleton pattern
    Ensures only one BERT model is loaded regardless of how many instances are created
    """
    
    # Class-level variables (shared across all instances)
    _bert_instance = None
    _bert_available = None
    
    def __init__(self):
        # Load BERT only once across all instances
        if BERTConfidenceBooster._bert_instance is None:
            try:
                logger.info("Loading medical Spanish BERT model (singleton)...")
                BERTConfidenceBooster._bert_instance = MedicalSpanishBERT()
                BERTConfidenceBooster._bert_available = True
                logger.info("BERT model loaded successfully and cached for reuse")
            except Exception as e:
                logger.warning(f"BERT model failed to load: {e}")
                BERTConfidenceBooster._bert_available = False
                BERTConfidenceBooster._bert_instance = None
        
        # Set instance variables to class variables
        self.bert = BERTConfidenceBooster._bert_instance
        self.bert_available = BERTConfidenceBooster._bert_available
    
    async def boost_medication_confidence(self, medications: List[Dict], original_text: str) -> List[Dict]:
        """
        Boost confidence when BERT agrees with your extraction
        
        Args:
            medications: List of medications from your existing extraction system
            original_text: Original Spanish text being analyzed
            
        Returns:
            Enhanced medications with BERT confidence boosts applied
        """
        if not self.bert_available:
            logger.debug("BERT unavailable, returning original medications")
            return medications
        
        try:
            # Get BERT's analysis of the text
            bert_result = await self.bert.extract_medical_entities(original_text)
            
            # Extract medication terms that BERT identified
            bert_medication_terms = {
                entity.spanish_term.lower() 
                for entity in bert_result.entities 
                if entity.entity_type == "medication"
            }
            
            if not bert_medication_terms:
                logger.debug("BERT found no medication entities, no confidence boost applied")
                # Add bert_boost field even when no boost applied for consistency
                for med in medications:
                    med["bert_boost"] = 0.0
                    med["bert_agreement"] = False
                return medications
            
            logger.debug(f"BERT detected medication terms: {bert_medication_terms}")
            
            # Boost confidence for medications BERT also identified
            enhanced_medications = []
            for med in medications:
                med_copy = med.copy()
                original_term = med["original_term"].lower()
                
                # Check if BERT also detected this medication
                bert_agreement = any(
                    bert_term in original_term or original_term in bert_term 
                    for bert_term in bert_medication_terms
                )
                
                if bert_agreement:
                    # Calculate confidence boost (up to 0.15, never exceed 1.0)
                    current_confidence = med_copy["extraction_confidence"]
                    boost = min(0.15, 1.0 - current_confidence)
                    
                    med_copy["extraction_confidence"] = current_confidence + boost
                    med_copy["bert_boost"] = boost
                    med_copy["bert_agreement"] = True
                    
                    logger.debug(f"BERT boost applied to '{original_term}': +{boost:.3f} confidence")
                else:
                    med_copy["bert_boost"] = 0.0
                    med_copy["bert_agreement"] = False
                
                enhanced_medications.append(med_copy)
            
            logger.info(f"BERT confidence boost completed: {len(enhanced_medications)} medications processed")
            return enhanced_medications
            
        except Exception as e:
            logger.warning(f"BERT confidence boost failed: {e}")
            # Return original medications with bert_boost field for consistency
            for med in medications:
                med["bert_boost"] = 0.0
                med["bert_agreement"] = False
            return medications
    
    def get_bert_status(self) -> Dict:
        """
        Get current BERT availability status for debugging
        
        Returns:
            Dict with BERT status information
        """
        return {
            "bert_available": self.bert_available,
            "bert_model_loaded": BERTConfidenceBooster._bert_instance is not None,
            "model_type": "PlanTL-GOB-ES/roberta-base-biomedical-clinical-es" if self.bert_available else None
        }
    
    @classmethod
    def reset_bert_instance(cls):
        """
        Reset the singleton instance (useful for testing)
        """
        cls._bert_instance = None
        cls._bert_available = None
        logger.info("BERT singleton instance reset")