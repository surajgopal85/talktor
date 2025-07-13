# =============================================================================
# services/medical_intelligence/confidence.py
# =============================================================================

import logging
from typing import Dict

logger = logging.getLogger(__name__)

class ConfidenceScorer:
    """
    Calculates confidence scores for medication extractions
    Uses multiple signals for learning-ready scoring
    """
    
    def __init__(self):
        self.medication_indicators = [
            "taking", "prescribed", "medication", "medicine", "drug", "pill", 
            "tablet", "dosage", "mg", "milligram", "daily", "twice", "morning",
            "doctor", "physician", "pharmacy", "prescription"
        ]
        
        self.strategy_weights = {
            "pattern_match": 0.15,
            "single_word": 0.05,
            "bigram": 0.0
        }
    
    def calculate_confidence(self, candidate: Dict, api_result: Dict, original_text: str) -> float:
        """Calculate extraction confidence using multiple factors"""
        confidence = 0.0
        
        # API-based confidence (40% of total)
        confidence += self._calculate_api_confidence(api_result)
        
        # Context-based confidence (20% of total)
        confidence += self._calculate_context_confidence(candidate)
        
        # Strategy-based confidence (15% of total)
        confidence += self._calculate_strategy_confidence(candidate)
        
        # Position and length confidence (10% of total)
        confidence += self._calculate_position_confidence(candidate, original_text)
        
        # Pattern-specific bonus (15% of total)
        confidence += self._calculate_pattern_confidence(candidate)
        
        return min(confidence, 1.0)  # Cap at 1.0
    
    def _calculate_api_confidence(self, api_result: Dict) -> float:
        """Calculate confidence based on API response richness"""
        confidence = 0.0
        
        if api_result.get("canonical_name"):
            confidence += 0.4
            
            # Bonus for rich API data
            if api_result.get("indications"):
                confidence += 0.1
            if api_result.get("contraindications"):
                confidence += 0.1
            if api_result.get("rxcui"):  # RxNorm ID means high confidence
                confidence += 0.1
        
        return confidence
    
    def _calculate_context_confidence(self, candidate: Dict) -> float:
        """Calculate confidence based on surrounding context"""
        context = candidate["context"].lower()
        
        context_matches = sum(1 for indicator in self.medication_indicators if indicator in context)
        return min(context_matches * 0.05, 0.2)  # Up to 0.2 bonus
    
    def _calculate_strategy_confidence(self, candidate: Dict) -> float:
        """Calculate confidence based on extraction strategy"""
        strategy = candidate["strategy"]
        return self.strategy_weights.get(strategy, 0)
    
    def _calculate_position_confidence(self, candidate: Dict, original_text: str) -> float:
        """Calculate confidence based on position and length"""
        confidence = 0.0
        
        # Position confidence (medications often appear in middle of sentence)
        position_ratio = candidate["position"] / max(len(original_text.split()), 1)
        if 0.2 < position_ratio < 0.8:
            confidence += 0.05
        
        # Length confidence (optimal medication name length)
        term_length = len(candidate["term"])
        if 4 <= term_length <= 15:
            confidence += 0.05
        
        return confidence
    
    def _calculate_pattern_confidence(self, candidate: Dict) -> float:
        """Calculate confidence for pattern-matched candidates"""
        confidence_modifiers = candidate.get("confidence_modifiers", {})
        
        if confidence_modifiers.get("pattern_matched"):
            pattern_confidence = confidence_modifiers.get("pattern_confidence", 0)
            return pattern_confidence * 0.15  # 15% max from pattern matching
        
        return 0.0