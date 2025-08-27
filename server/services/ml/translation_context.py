# services/ml/translation_context.py  
# Simple translation context hints using BERT

from typing import Dict
from .medical_bert import MedicalSpanishBERT

class SimpleTranslationContext:
    """
    Simple translation context detection - just medical vs general
    Replaces: translation_enhancer.py, context_analyzer.py
    """
    
    def __init__(self):
        self.bert_available = True
        try:
            self.bert = MedicalSpanishBERT()
        except:
            self.bert_available = False
    
    async def get_context_hint(self, spanish_text: str) -> Dict:
        """
        Simple context hint: medical or general
        """
        if not self.bert_available:
            return {"context": "unknown", "confidence": 0.0}
        
        try:
            bert_result = await self.bert.extract_medical_entities(spanish_text)
            medical_entities = len(bert_result.entities)
            
            is_medical = medical_entities > 0 and bert_result.bert_confidence > 0.5
            
            return {
                "context": "medical" if is_medical else "general",
                "confidence": bert_result.bert_confidence,
                "entities_found": medical_entities
            }
            
        except:
            return {"context": "unknown", "confidence": 0.0}