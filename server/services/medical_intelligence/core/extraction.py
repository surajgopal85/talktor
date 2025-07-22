# =============================================================================
# services/medical_intelligence/extraction.py
# =============================================================================

import re
import logging
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from .api_client import ExternalMedicalAPIClient
from .confidence import ConfidenceScorer
from .learning import LearningManager

logger = logging.getLogger(__name__)

class MedicationExtractionService:
    """
    Core medication extraction service with learning capabilities
    Handles multi-strategy extraction, API validation, and confidence scoring
    """
    
    def __init__(self):
        self.api_client = ExternalMedicalAPIClient()
        self.confidence_scorer = ConfidenceScorer()
        self.learning_manager = LearningManager()
        self.confidence_threshold = 0.3
        
    async def extract_medications(self, text: str, session_id: str, medical_context: str = "general") -> Dict:
        """Main extraction method with learning integration"""
        
        logger.info(f"🧠 MedicationExtractionService: Processing '{text}'")
        
        # Step 1: Identify candidates using multiple strategies
        candidates = await self._identify_candidates(text)
        logger.info(f"🔍 Found {len(candidates)} candidates")
        
        # Step 2: Validate candidates with external APIs
        validated_medications = await self._validate_candidates(candidates, medical_context, text)
        
        # Step 3: Generate extraction metadata
        metadata = self._generate_extraction_metadata(candidates, validated_medications, text)
        
        # Step 4: Store extraction data for learning
        extraction_id = await self.learning_manager.store_extraction_attempt(
            session_id, text, candidates, validated_medications, metadata
        )
        
        return {
            "medications": validated_medications,
            "metadata": metadata,
            "learning_data": {
                "session_id": session_id,
                "extraction_id": extraction_id,
                "ready_for_feedback": True
            }
        }
    
    async def _identify_candidates(self, text: str) -> List[Dict]:
        """Identify potential medication candidates using multiple strategies"""
        candidates = []
        words = re.findall(r'\b\w{3,}\b', text.lower())
        
        # Strategy 1: Single word extraction
        candidates.extend(self._extract_single_words(words))
        
        # Strategy 2: Bigram extraction (compound drug names)
        candidates.extend(self._extract_bigrams(words))
        
        # Strategy 3: Pattern-based extraction (pharmaceutical suffixes)
        candidates.extend(self._extract_by_patterns(text))
        
        # Strategy 4: Context-aware extraction (future enhancement)
        # candidates.extend(self._extract_context_aware(text, words))
        
        return self._deduplicate_candidates(candidates)
    
    def _extract_single_words(self, words: List[str]) -> List[Dict]:
        """Extract single-word medication candidates"""
        candidates = []
        
        for i, word in enumerate(words):
            if len(word) >= 4:  # Filter very short words
                candidates.append({
                    "term": word,
                    "strategy": "single_word",
                    "context": " ".join(words[max(0,i-2):i+3]),
                    "position": i,
                    "confidence_modifiers": {
                        "word_length": len(word),
                        "position_ratio": i / len(words) if words else 0
                    }
                })
        
        return candidates
    
    def _extract_bigrams(self, words: List[str]) -> List[Dict]:
        """Extract two-word medication candidates (e.g., 'birth control')"""
        candidates = []
        
        for i in range(len(words)-1):
            bigram = f"{words[i]} {words[i+1]}"
            candidates.append({
                "term": bigram,
                "strategy": "bigram",
                "context": " ".join(words[max(0,i-1):i+4]),
                "position": i,
                "confidence_modifiers": {
                    "compound_length": len(bigram),
                    "first_word_length": len(words[i])
                }
            })
        
        return candidates
    
    def _extract_by_patterns(self, text: str) -> List[Dict]:
        """Extract medications using known pharmaceutical patterns"""
        candidates = []
        
        # Common medication suffix patterns with confidence weights
        patterns = {
            r'\b\w+mycin\b': 0.8,    # antibiotics (azithromycin, erythromycin)
            r'\b\w+cillin\b': 0.85,  # penicillin family
            r'\b\w+prazole\b': 0.9,  # proton pump inhibitors
            r'\b\w+statin\b': 0.85,  # cholesterol medications
            r'\b\w+pril\b': 0.8,     # ACE inhibitors (lisinopril)
            r'\b\w+lol\b': 0.75,     # beta blockers (metoprolol)
            r'\b\w+ide\b': 0.7,      # diuretics (furosemide)
            r'\b\w+pine\b': 0.7,     # calcium channel blockers
        }
        
        for pattern, pattern_confidence in patterns.items():
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                term = match.group()
                word_position = len(text[:match.start()].split())
                
                candidates.append({
                    "term": term,
                    "strategy": "pattern_match",
                    "context": text[max(0, match.start()-20):match.end()+20],
                    "position": word_position,
                    "confidence_modifiers": {
                        "pattern_matched": True,
                        "pattern_confidence": pattern_confidence,
                        "suffix_type": pattern
                    }
                })
        
        return candidates
    
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
    
    async def _validate_candidates(self, candidates: List[Dict], medical_context: str, original_text: str) -> List[Dict]:
        """Validate candidates using external medical APIs"""
        validated_medications = []
        
        for candidate in candidates:
            try:
                # Use API client to lookup medication
                api_result = await self.api_client.lookup_medication(candidate["term"], medical_context)
                
                # Calculate confidence score
                confidence_score = self.confidence_scorer.calculate_confidence(
                    candidate, api_result, original_text
                )
                
                # Filter by confidence threshold
                if confidence_score > self.confidence_threshold:
                    validated_medications.append({
                        "medication": api_result,
                        "extraction_confidence": confidence_score,
                        "extraction_strategy": candidate["strategy"],
                        "context": candidate["context"],
                        "position": candidate["position"],
                        "original_term": candidate["term"],
                        "validation_timestamp": datetime.now().isoformat()
                    })
                    
            except Exception as e:
                logger.warning(f"⚠️ API validation failed for '{candidate['term']}': {e}")
                continue
        
        return validated_medications
    
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