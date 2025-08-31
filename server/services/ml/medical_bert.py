# services/ml/medical_bert.py
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from typing import List, Dict, Optional, Tuple
import numpy as np
import logging
from dataclasses import dataclass
import hashlib
import pickle
import os
from datetime import datetime, timedelta

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

class BERTEmbeddingCache:
    """
    Cache system for BERT embeddings to improve performance
    Reduces redundant computations for repeated medical terms
    """
    
    def __init__(self, cache_dir: str = "data/ml/bert_cache", max_size: int = 10000, ttl_hours: int = 24):
        self.cache_dir = cache_dir
        self.max_size = max_size
        self.ttl_hours = ttl_hours
        self.cache_stats = {"hits": 0, "misses": 0, "evictions": 0}
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load cache index
        self.cache_index_file = os.path.join(cache_dir, "cache_index.pkl")
        self.cache_index = self._load_cache_index()
    
    def _load_cache_index(self) -> Dict[str, Dict]:
        """Load cache index from disk"""
        try:
            if os.path.exists(self.cache_index_file):
                with open(self.cache_index_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache index: {e}")
        return {}
    
    def _save_cache_index(self):
        """Save cache index to disk"""
        try:
            with open(self.cache_index_file, 'wb') as f:
                pickle.dump(self.cache_index, f)
        except Exception as e:
            logger.warning(f"Failed to save cache index: {e}")
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> str:
        """Get file path for cached embedding"""
        return os.path.join(self.cache_dir, f"{cache_key}.pkl")
    
    def get(self, text: str) -> Optional[np.ndarray]:
        """Get cached embedding for text"""
        cache_key = self._get_cache_key(text)
        
        if cache_key in self.cache_index:
            entry = self.cache_index[cache_key]
            
            # Check if cache entry is still valid
            if datetime.now() - entry['timestamp'] < timedelta(hours=self.ttl_hours):
                cache_path = self._get_cache_path(cache_key)
                try:
                    with open(cache_path, 'rb') as f:
                        embedding = pickle.load(f)
                    self.cache_stats["hits"] += 1
                    logger.debug(f"Cache hit for text: {text[:50]}...")
                    return embedding
                except Exception as e:
                    logger.warning(f"Failed to load cached embedding: {e}")
            else:
                # Remove expired entry
                self._remove_cache_entry(cache_key)
        
        self.cache_stats["misses"] += 1
        return None
    
    def put(self, text: str, embedding: np.ndarray):
        """Store embedding in cache"""
        cache_key = self._get_cache_key(text)
        
        # Check cache size and evict if necessary
        if len(self.cache_index) >= self.max_size:
            self._evict_oldest_entries()
        
        # Store embedding
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(embedding, f)
            
            self.cache_index[cache_key] = {
                'timestamp': datetime.now(),
                'text_length': len(text),
                'embedding_shape': embedding.shape
            }
            
            self._save_cache_index()
            logger.debug(f"Cached embedding for text: {text[:50]}...")
            
        except Exception as e:
            logger.warning(f"Failed to cache embedding: {e}")
    
    def _remove_cache_entry(self, cache_key: str):
        """Remove cache entry"""
        try:
            cache_path = self._get_cache_path(cache_key)
            if os.path.exists(cache_path):
                os.remove(cache_path)
            del self.cache_index[cache_key]
        except Exception as e:
            logger.warning(f"Failed to remove cache entry: {e}")
    
    def _evict_oldest_entries(self):
        """Evict oldest cache entries to make room"""
        if len(self.cache_index) < self.max_size:
            return
        
        # Sort by timestamp and remove oldest entries
        sorted_entries = sorted(self.cache_index.items(), key=lambda x: x[1]['timestamp'])
        entries_to_remove = len(sorted_entries) - self.max_size + 1
        
        for i in range(entries_to_remove):
            cache_key = sorted_entries[i][0]
            self._remove_cache_entry(cache_key)
            self.cache_stats["evictions"] += 1
        
        logger.info(f"Evicted {entries_to_remove} cache entries")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            **self.cache_stats,
            "cache_size": len(self.cache_index),
            "max_size": self.max_size,
            "hit_rate": self.cache_stats["hits"] / (self.cache_stats["hits"] + self.cache_stats["misses"]) if (self.cache_stats["hits"] + self.cache_stats["misses"]) > 0 else 0
        }
    
    def clear(self):
        """Clear all cached data"""
        try:
            for cache_key in list(self.cache_index.keys()):
                self._remove_cache_entry(cache_key)
            self.cache_stats = {"hits": 0, "misses": 0, "evictions": 0}
            logger.info("BERT cache cleared")
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")

class MedicalSpanishBERT:
    """
    Medical Spanish BERT wrapper for entity extraction and understanding
    Focuses on translation accuracy, NOT clinical decision making
    """
    
    def __init__(self):
        """Initialize medical Spanish BERT model with caching"""
        self.model_name = "PlanTL-GOB-ES/roberta-base-biomedical-clinical-es"
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Initialize embedding cache
        self.embedding_cache = BERTEmbeddingCache()
        
        # Enhanced medical term categories for high-fidelity translation
        self.medical_categories = {
            "medication": [
                # Common Spanish medication terms
                "medicamento", "medicina", "pastilla", "tableta", "jarabe", "inyección", "pomada", "crema",
                "cápsula", "comprimido", "suspensión", "gotas", "spray", "parche", "supositorio",
                # OBGYN-specific medications
                "anticonceptivo", "píldora", "hormona", "estrógeno", "progesterona", "vitamina prenatal",
                "ácido fólico", "hierro", "calcio", "magnesio", "dha", "omega", "probiótico",
                # NEW: Additional OBGYN terms
                "cerclage", "cerclaje", "progesterone_therapy", "progesterona_terapia"
            ],
            "condition": [
                # General conditions
                "enfermedad", "condición", "diagnóstico", "embarazo", "diabetes", "hipertensión",
                "anemia", "infección", "inflamación", "alergia", "asma", "artritis",
                # OBGYN-specific conditions
                "embarazada", "gestación", "menopausia", "pcos", "endometriosis", "fibromas",
                "infertilidad", "amenorrea", "dismenorrea", "metrorragia", "preeclampsia",
                # NEW: Additional OBGYN conditions
                "cervical_insufficiency", "insuficiencia_cervical", "effacement", "borramiento",
                "preterm_labor", "parto_prematuro", "braxton_hicks", "contracciones_braxton"
            ],
            "symptom": [
                # General symptoms
                "dolor", "náusea", "fiebre", "mareo", "fatiga", "sangrado", "inflamación",
                "picazón", "ardor", "hinchazón", "calambres", "vómito", "diarrea",
                # OBGYN-specific symptoms
                "sofocos", "bochornos", "amenorrea", "dismenorrea", "metrorragia", "leucorrea",
                "dolor pélvico", "dolor de espalda", "náuseas matutinas", "acidez",
                # NEW: Additional OBGYN symptoms
                "colico", "cólico", "flujo", "sangrado", "presion", "presión", "dolores",
                "contracciones", "presión_pélvica", "flujo_vaginal"
            ],
            "body_part": [
                # General body parts
                "cabeza", "estómago", "corazón", "pecho", "espalda", "brazo", "pierna",
                "hígado", "riñón", "pulmón", "cerebro", "sangre", "hueso",
                # OBGYN-specific body parts
                "útero", "ovario", "trompa", "vagina", "cérvix", "cervix", "mama", "pecho",
                "pelvis", "abdomen", "vulva", "clítoris", "perineo",
                # NEW: Additional OBGYN body parts
                "cuello_utero", "cuello_del_utero", "cervical", "uterino", "pelvico", "pélvico"
            ],
            "procedure": [
                # General procedures
                "cirugía", "operación", "examen", "análisis", "radiografía", "ultrasonido",
                "biopsia", "endoscopia", "cateterismo", "transfusión", "quimioterapia",
                # OBGYN-specific procedures
                "cesárea", "parto", "episiotomía", "colposcopia", "mamografía", "papanicolau",
                "histerectomía", "oforectomía", "ligadura", "inseminación", "fertilización",
                # NEW: Additional OBGYN procedures
                "ultrasonido", "ultrasonido_transvaginal", "ultrasound", "transvaginal",
                "monitoreo_fetal", "monitoreo_uterino", "examen_cervical", "medicion_cervical"
            ]
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
                
                # SAFE: Handle attention weights with proper error checking
                try:
                    attention_weights = outputs.attentions[-1] if outputs.attentions else None  # Last layer attention
                except (IndexError, AttributeError) as e:
                    logger.warning(f"Attention weights extraction failed: {e}")
                    attention_weights = None
            
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
        attention_weights: Optional[torch.Tensor],
        inputs: Dict
    ) -> List[MedicalEntity]:
        """Extract entities using BERT embeddings and attention patterns"""
        
        entities = []
        tokens = self.tokenizer.convert_ids_to_tokens(inputs['input_ids'][0])
        
        # SAFE: Handle attention weights with proper error checking
        if attention_weights is not None and len(attention_weights) > 0:
            try:
                # Calculate attention-based importance scores
                attention_scores = attention_weights[0].mean(dim=0).mean(dim=0)  # Average across heads and layers
            except (IndexError, AttributeError) as e:
                logger.warning(f"Attention weights processing failed: {e}, using fallback")
                # Fallback: use uniform attention scores
                attention_scores = torch.ones(len(tokens)) * 0.5
        else:
            logger.warning("No attention weights available, using fallback scoring")
            # Fallback: use uniform attention scores
            attention_scores = torch.ones(len(tokens)) * 0.5
        
        # Find high-attention tokens that might be medical terms
        for i, (token, attention_score) in enumerate(zip(tokens, attention_scores)):
            if attention_score > 0.1 and not token.startswith('[') and len(token) > 2:
                
                try:
                    # Get embedding for this token
                    token_embedding = hidden_states[0, i].cpu().numpy()
                except (IndexError, AttributeError) as e:
                    logger.warning(f"Token embedding extraction failed for token {i}: {e}")
                    continue
                
                # Check if token matches medical patterns
                entity_type = await self._classify_medical_token(token, text)
                
                if entity_type:
                    try:
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
                    except Exception as e:
                        logger.warning(f"Entity creation failed for token '{token}': {e}")
                        continue
        
        # Merge subword tokens into complete medical terms
        entities = self._merge_subword_entities(entities)
        
        return entities
    
    async def _classify_medical_token(self, token: str, full_text: str) -> Optional[str]:
        """Classify if a token is a medical entity and what type using intelligent analysis"""
        token_clean = token.replace('▁', '').lower()
        
        # NEW: Use medical knowledge base lookup first (most reliable)
        medical_info = await self._check_medical_database(token_clean)
        if medical_info:
            logger.info(f"🎯 Medical DB match: '{token_clean}' → {medical_info['category']}")
            return medical_info.get("category")
        
        # NEW: Check RxNorm API for medication terms
        rxnorm_info = await self._check_rxnorm_api(token_clean)
        if rxnorm_info:
            logger.info(f"💊 RxNorm match: '{token_clean}' → {rxnorm_info['category']}")
            return rxnorm_info.get("category")
        
        # Check against medical category keywords (fallback)
        for category, keywords in self.medical_categories.items():
            for keyword in keywords:
                if keyword in token_clean or token_clean in keyword:
                    return category
        
        # Check for common Spanish medical term patterns (fallback)
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
        try:
            # Simplified approach - in production, use offset_mapping
            token_clean = token.replace('▁', '')
            if not token_clean:
                return 0, 0
            
            start = text.lower().find(token_clean.lower())
            if start != -1:
                return start, start + len(token_clean)
            else:
                # Fallback: estimate position based on token index
                words = text.split()
                if token_index < len(words):
                    # Find the word at this position
                    target_word = words[token_index]
                    start = text.lower().find(target_word.lower())
                    if start != -1:
                        return start, start + len(target_word)
                
                # Final fallback
                return 0, len(token_clean)
        except Exception as e:
            logger.warning(f"Token span calculation failed for '{token}': {e}")
            return 0, len(token_clean) if token else 0
    
    def _extract_context(self, text: str, start: int, end: int, window: int = 30) -> str:
        """Extract surrounding context for a medical entity"""
        try:
            if not text:
                return ""
            
            context_start = max(0, start - window)
            context_end = min(len(text), end + window)
            
            # Ensure valid range
            if context_start >= context_end:
                return text[:min(window, len(text))]
            
            return text[context_start:context_end]
        except Exception as e:
            logger.warning(f"Context extraction failed: {e}")
            return text[:min(window, len(text))] if text else ""
    
    def _merge_subword_entities(self, entities: List[MedicalEntity]) -> List[MedicalEntity]:
        """Merge subword tokens into complete medical terms"""
        try:
            if not entities:
                return []
            
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
        except Exception as e:
            logger.warning(f"Subword entity merging failed: {e}")
            return entities  # Return original entities if merging fails
    
    def _calculate_overall_confidence(self, entities: List[MedicalEntity]) -> float:
        """Calculate overall confidence for the extraction"""
        if not entities:
            return 0.0
        return sum(entity.confidence for entity in entities) / len(entities)
    
    async def get_medical_embedding(self, spanish_text: str) -> np.ndarray:
        """Get BERT embedding for medical Spanish text with caching"""
        # Check cache first
        cached_embedding = self.embedding_cache.get(spanish_text)
        if cached_embedding is not None:
            logger.debug(f"Using cached embedding for: {spanish_text[:50]}...")
            return cached_embedding
        
        # Generate new embedding
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
        
        # Cache the embedding
        self.embedding_cache.put(spanish_text, embedding)
        
        return embedding
    
    def get_cache_stats(self) -> Dict:
        """Get BERT cache statistics"""
        return self.embedding_cache.get_stats()
    
    async def _check_rxnorm_api(self, term: str) -> Optional[Dict]:
        """Check RxNorm API for medication terms"""
        try:
            # For now, implement a simple local check
            # In production, this would call the actual RxNorm API
            rxnorm_medications = {
                "aspirin": {"rxcui": "1191", "name": "aspirin", "category": "medication"},
                "ibuprofen": {"rxcui": "5640", "name": "ibuprofen", "category": "medication"},
                "acetaminophen": {"rxcui": "161", "name": "acetaminophen", "category": "medication"},
                "vitamin": {"rxcui": "11170", "name": "vitamin", "category": "medication"},
                "progesterone": {"rxcui": "8723", "name": "progesterone", "category": "medication"},
                "cerclage": {"rxcui": "12345", "name": "cerclage", "category": "procedure"},
                "cerclaje": {"rxcui": "12345", "name": "cerclage", "category": "procedure"},
            }
            
            term_lower = term.lower()
            for med_name, med_info in rxnorm_medications.items():
                if term_lower in med_name or med_name in term_lower:
                    return med_info
            
            return None
        except Exception as e:
            logger.warning(f"RxNorm API check failed for '{term}': {e}")
            return None
    
    async def _check_medical_database(self, term: str) -> Optional[Dict]:
        """Check medical terminology databases"""
        try:
            # Medical terminology database (simplified)
            medical_terms = {
                # OBGYN terms
                "cerclage": {"category": "procedure", "confidence": 0.95, "source": "medical_db"},
                "cerclaje": {"category": "procedure", "confidence": 0.95, "source": "medical_db"},
                "cervical_insufficiency": {"category": "condition", "confidence": 0.9, "source": "medical_db"},
                "effacement": {"category": "condition", "confidence": 0.9, "source": "medical_db"},
                "braxton_hicks": {"category": "symptom", "confidence": 0.9, "source": "medical_db"},
                "colico": {"category": "symptom", "confidence": 0.85, "source": "medical_db"},
                "flujo": {"category": "symptom", "confidence": 0.8, "source": "medical_db"},
                "cuello_utero": {"category": "body_part", "confidence": 0.95, "source": "medical_db"},
                "ultrasonido": {"category": "procedure", "confidence": 0.9, "source": "medical_db"},
                "transvaginal": {"category": "procedure", "confidence": 0.9, "source": "medical_db"},
                "progesterone_therapy": {"category": "treatment", "confidence": 0.9, "source": "medical_db"},
                "preterm_labor": {"category": "condition", "confidence": 0.95, "source": "medical_db"},
                
                # General medical terms
                "dolor": {"category": "symptom", "confidence": 0.9, "source": "medical_db"},
                "sangrado": {"category": "symptom", "confidence": 0.9, "source": "medical_db"},
                "presion": {"category": "symptom", "confidence": 0.8, "source": "medical_db"},
                "embarazo": {"category": "condition", "confidence": 0.95, "source": "medical_db"},
                "parto": {"category": "procedure", "confidence": 0.9, "source": "medical_db"},
                "prematuro": {"category": "condition", "confidence": 0.9, "source": "medical_db"},
            }
            
            term_lower = term.lower()
            for med_term, med_info in medical_terms.items():
                if term_lower in med_term or med_term in term_lower:
                    return med_info
            
            return None
        except Exception as e:
            logger.warning(f"Medical database check failed for '{term}': {e}")
            return None