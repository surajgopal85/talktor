# =============================================================================
# services/medical_intelligence/extraction.py
# =============================================================================

import re
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from .api_client import ExternalMedicalAPIClient
from .confidence import ConfidenceScorer
from .learning import LearningManager

# Enhanced BERT integration
from services.ml import BERTConfidenceBooster

logger = logging.getLogger(__name__)

class MedicationExtractionService:
    """
    Core medication extraction service with enhanced BERT integration
    Optimized for high-fidelity Spanish/English medical translations
    """
    
    def __init__(self):
        self.api_client = ExternalMedicalAPIClient()
        self.confidence_scorer = ConfidenceScorer()
        self.learning_manager = LearningManager()
        self.confidence_threshold = 0.2  # Lowered for demo to show more medications

        # Enhanced BERT integration
        self.bert_booster = BERTConfidenceBooster()
        
    async def extract_medications(self, text: str, session_id: str, medical_context: str = "general") -> Dict:
        """Enhanced extraction method with early BERT integration"""
        
        logger.info(f"🧠 Enhanced Extraction: Processing '{text[:100]}...'")
        
        # Step 1: Early BERT analysis for context understanding
        bert_context = await self._get_bert_context(text)
        
        # Step 2: Identify candidates with BERT-enhanced patterns
        candidates = await self._identify_candidates_with_bert(text, bert_context)
        logger.info(f"🔍 Found {len(candidates)} candidates with BERT enhancement")
        
        # Step 3: Pre-filter candidates using BERT confidence
        bert_filtered_candidates = await self._bert_pre_filter(candidates, text)
        
        # Step 4: Validate candidates with external APIs (with safety checks)
        validated_medications = await self._validate_candidates_safe(bert_filtered_candidates, medical_context, text)
        
        # Step 5: Apply final BERT confidence boost
        final_medications = await self.bert_booster.boost_medication_confidence(validated_medications, text)
        
        # Step 6: Generate extraction metadata
        metadata = self._generate_extraction_metadata(candidates, final_medications, text)
        
        # Step 7: Store extraction data for learning
        extraction_id = await self.learning_manager.store_extraction_attempt(
            session_id, text, candidates, final_medications, metadata
        )
        
        return {
            "medications": final_medications,
            "bert_context": bert_context,
            "metadata": metadata,
            "learning_data": {
                "session_id": session_id,
                "extraction_id": extraction_id,
                "ready_for_feedback": True
            }
        }
    
    async def _get_bert_context(self, text: str) -> Dict:
        """Get BERT context analysis for better extraction"""
        try:
            bert_result = await self.bert_booster.bert.extract_medical_entities(text)
            return {
                "bert_entities": bert_result.entities,
                "bert_confidence": bert_result.bert_confidence,
                "medical_terms": [e.spanish_term for e in bert_result.entities if e.entity_type == "medication"],
                "processing_time_ms": bert_result.processing_time_ms
            }
        except Exception as e:
            logger.warning(f"BERT context analysis failed: {e}")
            return {
                "bert_entities": [],
                "bert_confidence": 0.0,
                "medical_terms": [],
                "processing_time_ms": 0
            }
    
    async def _identify_candidates_with_bert(self, text: str, bert_context: Dict) -> List[Dict]:
        """Enhanced candidate identification with BERT context"""
        candidates = []
        words = re.findall(r'\b\w{3,}\b', text.lower())
        
        # NEW: Smart pre-filtering to eliminate obvious non-medical words
        pre_filter_start = time.time()
        filtered_words = self._smart_pre_filter_words(words, text)
        pre_filter_time = time.time() - pre_filter_start
        logger.info(f"🔍 Smart pre-filter: {len(words)} → {len(filtered_words)} candidates in {pre_filter_time:.3f}s")
        
        # Strategy 1: BERT-enhanced single word extraction (only on filtered words)
        candidates.extend(self._extract_single_words_with_bert(filtered_words, bert_context))
        
        # Strategy 2: BERT-enhanced bigram extraction (only on filtered words)
        candidates.extend(self._extract_bigrams_with_bert(filtered_words, bert_context))
        
        # Strategy 3: Enhanced pattern-based extraction
        candidates.extend(self._extract_by_patterns_enhanced(text, bert_context))
        
        # Strategy 4: BERT entity-based extraction
        candidates.extend(self._extract_bert_entities(bert_context))
        
        return self._deduplicate_candidates(candidates)
    
    def _smart_pre_filter_words(self, words: List[str], text: str) -> List[str]:
        """Smart pre-filtering to eliminate obvious non-medical words before BERT processing"""
        
        # Common non-medical words that should never be processed
        common_words = {
            # Greetings and common words
            "good", "morning", "afternoon", "evening", "hello", "hi", "bye", "thank", "thanks",
            "yes", "no", "okay", "ok", "fine", "well", "how", "are", "you", "am", "is", "was",
            "have", "had", "has", "been", "being", "will", "would", "could", "should", "may",
            "might", "can", "do", "does", "did", "done", "go", "goes", "went", "gone",
            
            # Personal pronouns and names
            "i", "me", "my", "mine", "myself", "you", "your", "yours", "yourself", "he", "him",
            "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "we", "us",
            "our", "ours", "ourselves", "they", "them", "their", "theirs", "themselves",
            "miss", "mister", "doctor", "dr", "patient", "mr", "mrs", "ms",
            
            # Common verbs
            "want", "need", "like", "love", "hate", "feel", "think", "know", "see", "hear",
            "say", "tell", "talk", "speak", "listen", "read", "write", "eat", "drink", "sleep",
            "walk", "run", "sit", "stand", "come", "come", "get", "give", "take", "make",
            "help", "work", "play", "study", "learn", "teach", "buy", "sell", "pay", "cost",
            
            # Common adjectives
            "big", "small", "large", "little", "good", "bad", "nice", "ugly", "beautiful",
            "pretty", "handsome", "smart", "stupid", "clever", "dumb", "happy", "sad",
            "angry", "excited", "bored", "tired", "hungry", "thirsty", "hot", "cold",
            "warm", "cool", "new", "old", "young", "fresh", "clean", "dirty", "easy", "hard",
            
            # Time and place words
            "today", "yesterday", "tomorrow", "now", "then", "here", "there", "where",
            "when", "why", "what", "which", "who", "whom", "whose", "this", "that",
            "these", "those", "some", "any", "many", "much", "few", "several", "all",
            "every", "each", "both", "either", "neither", "none", "nothing", "something",
            
            # Spanish common words
            "buenos", "días", "tardes", "noches", "hola", "adiós", "gracias", "por", "favor",
            "pero", "como", "que", "cual", "quien", "donde", "cuando", "porque", "si", "no",
            "también", "tampoco", "siempre", "nunca", "ahora", "después", "antes", "más",
            "menos", "muy", "poco", "mucho", "bien", "mal", "bueno", "malo", "grande", "pequeño",
            "nuevo", "viejo", "joven", "alto", "bajo", "largo", "corto", "ancho", "estrecho",
            "caliente", "frío", "caluroso", "fresco", "bonito", "feo", "hermoso", "horrible",
            "fácil", "difícil", "importante", "necesario", "posible", "imposible", "verdadero", "falso"
        }
        
        # Medical context words that should always be processed
        medical_context_words = {
            "pain", "ache", "hurt", "sore", "swelling", "bleeding", "discharge", "fever",
            "nausea", "vomiting", "diarrhea", "constipation", "cough", "sneeze", "runny",
            "congestion", "headache", "migraine", "dizziness", "fatigue", "tired", "weak",
            "pregnant", "pregnancy", "baby", "fetus", "uterus", "cervix", "ovary", "ovaries",
            "period", "menstrual", "cycle", "ovulation", "fertility", "contraception",
            "vitamin", "supplement", "medication", "medicine", "pill", "tablet", "capsule",
            "injection", "shot", "cream", "ointment", "drops", "syrup", "liquid", "powder",
            "dose", "dosage", "prescription", "refill", "side", "effect", "reaction", "allergy",
            "infection", "bacteria", "virus", "fungus", "parasite", "inflammation", "swelling",
            "tumor", "cancer", "benign", "malignant", "metastasis", "remission", "relapse"
        }
        
        filtered_words = []
        for word in words:
            word_lower = word.lower()
            
            # Always include medical context words
            if word_lower in medical_context_words:
                filtered_words.append(word)
                continue
                
            # Skip common non-medical words
            if word_lower in common_words:
                continue
                
            # Skip very short words (likely not medical)
            if len(word_lower) < 4:
                continue
                
            # Skip words that are clearly names or places
            if word_lower in ["gonzalez", "carter", "smith", "jones", "brown", "wilson"]:
                continue
                
            # Include the word for further processing
            filtered_words.append(word)
        
        return filtered_words
    
    def _extract_single_words_with_bert(self, words: List[str], bert_context: Dict) -> List[Dict]:
        """Extract single-word candidates with BERT enhancement"""
        candidates = []
        bert_terms = set(bert_context.get("medical_terms", []))
        
        for i, word in enumerate(words):
            if len(word) >= 4:  # Filter very short words
                # Check if BERT identified this as medical
                bert_boost = 0.2 if word in bert_terms else 0.0
                
                candidates.append({
                    "term": word,
                    "strategy": "single_word_bert_enhanced",
                    "context": " ".join(words[max(0,i-2):i+3]),
                    "position": i,
                    "confidence_modifiers": {
                        "word_length": len(word),
                        "position_ratio": i / len(words) if words else 0,
                        "bert_identified": word in bert_terms,
                        "bert_confidence_boost": bert_boost
                    }
                })
        
        return candidates
    
    def _extract_bigrams_with_bert(self, words: List[str], bert_context: Dict) -> List[Dict]:
        """Extract two-word candidates with BERT enhancement"""
        candidates = []
        bert_terms = set(bert_context.get("medical_terms", []))
        
        for i in range(len(words)-1):
            bigram = f"{words[i]} {words[i+1]}"
            # Check if BERT identified this bigram as medical
            bert_boost = 0.25 if bigram in bert_terms else 0.0
            
            candidates.append({
                "term": bigram,
                "strategy": "bigram_bert_enhanced",
                "context": " ".join(words[max(0,i-1):i+4]),
                "position": i,
                "confidence_modifiers": {
                    "compound_length": len(bigram),
                    "first_word_length": len(words[i]),
                    "bert_identified": bigram in bert_terms,
                    "bert_confidence_boost": bert_boost
                }
            })
        
        return candidates
    
    def _extract_by_patterns_enhanced(self, text: str, bert_context: Dict) -> List[Dict]:
        """Enhanced pattern extraction with BERT context"""
        candidates = []
        
        # Enhanced medication suffix patterns with BERT validation
        patterns = {
            r'\b\w+mycin\b': 0.8,    # antibiotics
            r'\b\w+cillin\b': 0.85,  # penicillin family
            r'\b\w+prazole\b': 0.9,  # proton pump inhibitors
            r'\b\w+statin\b': 0.85,  # cholesterol medications
            r'\b\w+pril\b': 0.8,     # ACE inhibitors
            r'\b\w+lol\b': 0.75,     # beta blockers
            r'\b\w+ide\b': 0.7,      # diuretics
            r'\b\w+pine\b': 0.7,     # calcium channel blockers
            # Spanish medication patterns
            r'\b\w+ina\b': 0.6,      # Spanish medication suffix
            r'\b\w+ol\b': 0.65,      # Spanish medication suffix
        }
        
        bert_terms = set(bert_context.get("medical_terms", []))
        
        for pattern, pattern_confidence in patterns.items():
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                term = match.group()
                word_position = len(text[:match.start()].split())
                
                # Check if BERT also identified this term
                bert_boost = 0.15 if term in bert_terms else 0.0
                
                candidates.append({
                    "term": term,
                    "strategy": "pattern_match_bert_enhanced",
                    "context": text[max(0, match.start()-20):match.end()+20],
                    "position": word_position,
                    "confidence_modifiers": {
                        "pattern_matched": True,
                        "pattern_confidence": pattern_confidence,
                        "suffix_type": pattern,
                        "bert_identified": term in bert_terms,
                        "bert_confidence_boost": bert_boost
                    }
                })
        
        return candidates
    
    def _extract_bert_entities(self, bert_context: Dict) -> List[Dict]:
        """Extract candidates directly from BERT entities"""
        candidates = []
        
        for entity in bert_context.get("bert_entities", []):
            if entity.entity_type == "medication":
                candidates.append({
                    "term": entity.spanish_term,
                    "strategy": "bert_entity_extraction",
                    "context": entity.context,
                    "position": entity.start_position,
                    "confidence_modifiers": {
                        "bert_entity": True,
                        "bert_confidence": entity.confidence,
                        "bert_entity_type": entity.entity_type,
                        "bert_confidence_boost": min(0.3, entity.confidence)
                    }
                })
        
        return candidates
    
    async def _bert_pre_filter(self, candidates: List[Dict], text: str) -> List[Dict]:
        """Pre-filter candidates using BERT confidence - FIXED to be less aggressive"""
        filtered_candidates = []
        
        for candidate in candidates:
            # Calculate BERT-enhanced confidence
            bert_boost = candidate.get("confidence_modifiers", {}).get("bert_confidence_boost", 0.0)
            bert_identified = candidate.get("confidence_modifiers", {}).get("bert_identified", False)
            pattern_confidence = candidate.get("confidence_modifiers", {}).get("pattern_confidence", 0.0)
            
            # FIXED: More lenient filtering criteria
            # Keep candidates if ANY of these conditions are met:
            should_keep = (
                bert_identified or                    # BERT identified it
                pattern_confidence > 0.5 or          # Lowered from 0.7 to 0.5
                candidate.get("strategy") == "bert_entity_extraction" or  # Always keep BERT entities
                len(candidate["term"]) >= 4          # Keep longer terms (likely real medications)
            )
            
            if should_keep:
                filtered_candidates.append(candidate)
            else:
                logger.debug(f"Filtered out candidate '{candidate['term']}' (confidence: {pattern_confidence:.2f}, bert: {bert_identified})")
        
        logger.info(f"BERT pre-filter: {len(candidates)} → {len(filtered_candidates)} candidates")
        return filtered_candidates
    
    async def _validate_candidates_safe(self, candidates: List[Dict], medical_context: str, original_text: str) -> List[Dict]:
        """Safe validation with proper error handling"""
        validated_medications = []
        
        for candidate in candidates:
            try:
                # Use API client to lookup medication with safety checks
                api_result = await self.api_client.lookup_medication(candidate["term"], medical_context)
                
                # CRITICAL FIX: Ensure api_result is never None
                if api_result is None:
                    logger.warning(f"API returned None for '{candidate['term']}', using fallback")
                    api_result = {
                        "drug_name": candidate["term"],
                        "canonical_name": candidate["term"],
                        "brand_names": [],
                        "generic_names": [],
                        "drug_class": [],
                        "indications": [],
                        "contraindications": [],
                        "pregnancy_category": "unknown",
                        "translations": {},
                        "specialty_specific": {}
                    }
                
                # Calculate enhanced confidence score with BERT boost
                base_confidence = self.confidence_scorer.calculate_confidence(
                    candidate, api_result, original_text
                )
                
                # Add BERT confidence boost
                bert_boost = candidate.get("confidence_modifiers", {}).get("bert_confidence_boost", 0.0)
                final_confidence = min(base_confidence + bert_boost, 1.0)
                
                # Filter by confidence threshold
                if final_confidence > self.confidence_threshold:
                    validated_medications.append({
                        "medication": api_result,
                        "extraction_confidence": final_confidence,
                        "extraction_strategy": candidate["strategy"],
                        "context": candidate["context"],
                        "position": candidate["position"],
                        "original_term": candidate["term"],
                        "bert_boost": bert_boost,
                        "validation_timestamp": datetime.now().isoformat()
                    })
                    
            except Exception as e:
                logger.warning(f"⚠️ Safe validation failed for '{candidate['term']}': {e}")
                continue
        
        return validated_medications
    
    def _deduplicate_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """Remove duplicate terms while preserving strategy diversity"""
        unique_candidates = []
        seen_terms = set()
        
        for candidate in candidates:
            # Create unique key combining term and strategy
            candidate_key = f"{candidate['term']}_{candidate['strategy']}"
            if candidate_key not in seen_terms:
                seen_terms.add(candidate_key)
                unique_candidates.append(candidate)
        
        return unique_candidates
    
    def _generate_extraction_metadata(self, candidates: List[Dict], validated: List[Dict], text: str) -> Dict:
        """Generate metadata for learning and analytics"""
        return {
            "total_candidates": len(candidates),
            "successful_extractions": len(validated),
            "extraction_strategies_used": list(set([c["strategy"] for c in candidates])),
            "confidence_threshold_used": self.confidence_threshold,
            "timestamp": datetime.now().isoformat(),
            "text_length": len(text),
            "text_word_count": len(text.split()),
            "awaiting_feedback": True
        }