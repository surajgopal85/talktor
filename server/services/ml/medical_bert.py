# services/ml/medical_bert.py
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from typing import List, Dict, Optional, Tuple
import numpy as np
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MedicalEntity:
    """Represents a medical entity extracted from Spanish text"""
    spanish_term: str
    entity_type: str  # "medication", "condition", "symptom", "body_part", "procedure"
    confidence: float
    start_position: int
    end_position: int
    context: str
    bert_embedding: Optional[np.ndarray] = None

@dataclass
class ExtractionResult:
    """Results from medical entity extraction"""
    entities: List[MedicalEntity]
    processing_time_ms: float
    bert_confidence: float
    extraction_method: str

class MedicalSpanishBERT:
    """
    Medical Spanish BERT wrapper for entity extraction and understanding
    Focuses on translation accuracy, NOT clinical decision making
    """
    
    def __init__(self):
        """Initialize medical Spanish BERT model"""
        self.model_name = "PlanTL-GOB-ES/roberta-base-biomedical-clinical-es"
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Medical term categories for classification
        self.medical_categories = {
            "medication": ["medicamento", "medicina", "pastilla", "tableta", "jarabe", "inyección"],
            "condition": ["enfermedad", "condición", "diagnóstico", "embarazo", "diabetes", "hipertensión"],
            "symptom": ["dolor", "náusea", "fiebre", "mareo", "fatiga", "sangrado"],
            "body_part": ["cabeza", "estómago", "corazón", "pecho", "espalda", "brazo"],
            "procedure": ["cirugía", "operación", "examen", "análisis", "radiografía", "ultrasonido"]
        }
        
        self._load_model()
    
    def _load_model(self):
        """Load the medical Spanish BERT model"""
        try:
            logger.info(f"Loading medical Spanish BERT model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            logger.info("✅ Medical Spanish BERT loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load medical Spanish BERT: {e}")
            raise
    
    async def extract_medical_entities(self, spanish_text: str) -> ExtractionResult:
        """
        Extract medical entities from Spanish text using BERT
        Purpose: Improve translation accuracy, NOT clinical assessment
        """
        import time
        start_time = time.time()
        
        try:
            # Tokenize and encode
            inputs = self.tokenizer(
                spanish_text,
                return_tensors="pt",
                max_length=512,
                truncation=True,
                padding=True,
                return_offsets_mapping=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items() if k != 'offset_mapping'}
            
            # Get BERT embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                hidden_states = outputs.last_hidden_state
                attention_weights = outputs.attentions[-1]  # Last layer attention
            
            # Extract potential medical entities
            entities = await self._extract_entities_from_embeddings(
                spanish_text, hidden_states, attention_weights, inputs
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            return ExtractionResult(
                entities=entities,
                processing_time_ms=processing_time,
                bert_confidence=self._calculate_overall_confidence(entities),
                extraction_method="medical_spanish_bert"
            )
            
        except Exception as e:
            logger.error(f"❌ Medical entity extraction failed: {e}")
            return ExtractionResult(
                entities=[],
                processing_time_ms=0,
                bert_confidence=0.0,
                extraction_method="failed"
            )
    
    async def _extract_entities_from_embeddings(
        self,
        text: str,
        hidden_states: torch.Tensor,
        attention_weights: torch.Tensor,
        inputs: Dict
    ) -> List[MedicalEntity]:
        """Extract entities using BERT embeddings and attention patterns"""
        
        entities = []
        tokens = self.tokenizer.convert_ids_to_tokens(inputs['input_ids'][0])
        
        # Calculate attention-based importance scores
        attention_scores = attention_weights[0].mean(dim=0).mean(dim=0)  # Average across heads and layers
        
        # Find high-attention tokens that might be medical terms
        for i, (token, attention_score) in enumerate(zip(tokens, attention_scores)):
            if attention_score > 0.1 and not token.startswith('[') and len(token) > 2:
                
                # Get embedding for this token
                token_embedding = hidden_states[0, i].cpu().numpy()
                
                # Check if token matches medical patterns
                entity_type = await self._classify_medical_token(token, text)
                
                if entity_type:
                    # Find the actual text span for this token
                    start_pos, end_pos = self._find_token_span(token, text, i)
                    
                    entity = MedicalEntity(
                        spanish_term=token.replace('▁', ''),  # Remove subword markers
                        entity_type=entity_type,
                        confidence=float(attention_score),
                        start_position=start_pos,
                        end_position=end_pos,
                        context=self._extract_context(text, start_pos, end_pos),
                        bert_embedding=token_embedding
                    )
                    entities.append(entity)
        
        # Merge subword tokens into complete medical terms
        entities = self._merge_subword_entities(entities)
        
        return entities
    
    async def _classify_medical_token(self, token: str, full_text: str) -> Optional[str]:
        """Classify if a token is a medical entity and what type"""
        token_clean = token.replace('▁', '').lower()
        
        # Check against medical category keywords
        for category, keywords in self.medical_categories.items():
            for keyword in keywords:
                if keyword in token_clean or token_clean in keyword:
                    return category
        
        # Check for common Spanish medical term patterns
        medical_patterns = [
            'ibuprofeno', 'acetaminofén', 'aspirina',  # Common medications
            'embarazada', 'diabetes', 'hipertensión',  # Common conditions
            'dolor', 'náusea', 'fiebre',               # Common symptoms
        ]
        
        for pattern in medical_patterns:
            if pattern in token_clean:
                return self._get_category_for_pattern(pattern)
        
        return None
    
    def _get_category_for_pattern(self, pattern: str) -> str:
        """Get medical category for a specific pattern"""
        medication_patterns = ['ibuprofeno', 'acetaminofén', 'aspirina', 'vitamina']
        condition_patterns = ['embarazada', 'diabetes', 'hipertensión', 'embarazo']
        symptom_patterns = ['dolor', 'náusea', 'fiebre', 'mareo']
        
        if any(p in pattern for p in medication_patterns):
            return "medication"
        elif any(p in pattern for p in condition_patterns):
            return "condition"  
        elif any(p in pattern for p in symptom_patterns):
            return "symptom"
        else:
            return "unknown"
    
    def _find_token_span(self, token: str, text: str, token_index: int) -> Tuple[int, int]:
        """Find the character span of a token in the original text"""
        # Simplified approach - in production, use offset_mapping
        token_clean = token.replace('▁', '')
        start = text.lower().find(token_clean.lower())
        if start != -1:
            return start, start + len(token_clean)
        return 0, len(token_clean)
    
    def _extract_context(self, text: str, start: int, end: int, window: int = 30) -> str:
        """Extract surrounding context for a medical entity"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end]
    
    def _merge_subword_entities(self, entities: List[MedicalEntity]) -> List[MedicalEntity]:
        """Merge subword tokens into complete medical terms"""
        # Simplified merging - in production, implement proper subword reconstruction
        merged = []
        current_entity = None
        
        for entity in sorted(entities, key=lambda x: x.start_position):
            if current_entity and entity.start_position <= current_entity.end_position + 2:
                # Merge with current entity
                current_entity.spanish_term += entity.spanish_term
                current_entity.end_position = entity.end_position
                current_entity.confidence = max(current_entity.confidence, entity.confidence)
            else:
                if current_entity:
                    merged.append(current_entity)
                current_entity = entity
        
        if current_entity:
            merged.append(current_entity)
        
        return merged
    
    def _calculate_overall_confidence(self, entities: List[MedicalEntity]) -> float:
        """Calculate overall confidence for the extraction"""
        if not entities:
            return 0.0
        return sum(entity.confidence for entity in entities) / len(entities)
    
    async def get_medical_embedding(self, spanish_text: str) -> np.ndarray:
        """Get BERT embedding for medical Spanish text"""
        inputs = self.tokenizer(
            spanish_text,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use CLS token embedding as sentence representation
            embedding = outputs.last_hidden_state[0, 0].cpu().numpy()
        
        return embedding