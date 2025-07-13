# =============================================================================
# services/medical_intelligence/learning.py
# =============================================================================

import logging
from typing import Dict, List
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class LearningManager:
    """
    Manages learning data collection and reinforcement learning infrastructure
    Stores extraction attempts for future RL training
    """
    
    def __init__(self):
        # In production, this would connect to a database
        self.extraction_history = {}
        
    async def store_extraction_attempt(self, session_id: str, text: str, candidates: List[Dict], 
                                     validated_medications: List[Dict], metadata: Dict) -> str:
        """Store extraction attempt for learning"""
        
        extraction_id = str(uuid.uuid4())
        
        extraction_entry = {
            "extraction_id": extraction_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "original_text": text,
            "candidates_analyzed": [
                {
                    "term": c["term"],
                    "strategy": c["strategy"],
                    "position": c["position"]
                } for c in candidates
            ],
            "successful_extractions": [
                {
                    "term": r["original_term"],
                    "canonical_name": r["medication"].get("canonical_name"),
                    "confidence": r["extraction_confidence"],
                    "strategy": r["extraction_strategy"]
                } for r in validated_medications
            ],
            "metadata": metadata,
            "feedback_received": None,
            "learning_status": "pending_feedback"
        }
        
        self.extraction_history[extraction_id] = extraction_entry
        
        logger.info(f"📚 Stored extraction attempt {extraction_id} for learning")
        return extraction_id
    
    async def record_feedback(self, extraction_id: str, feedback: Dict[str, bool]) -> Dict:
        """Record doctor feedback on extraction accuracy"""
        
        if extraction_id not in self.extraction_history:
            raise Exception("Extraction not found")
        
        extraction = self.extraction_history[extraction_id]
        extraction["feedback_received"] = feedback
        extraction["learning_status"] = "feedback_received"
        extraction["feedback_timestamp"] = datetime.now().isoformat()
        
        logger.info(f"📝 Feedback recorded for extraction {extraction_id}: {feedback}")
        
        return {
            "message": "Feedback recorded successfully",
            "extraction_id": extraction_id,
            "feedback": feedback,
            "learning_status": "updated"
        }
    
    async def get_learning_analytics(self) -> Dict:
        """Get analytics for reinforcement learning"""
        
        total_extractions = len(self.extraction_history)
        feedback_received = len([e for e in self.extraction_history.values() 
                               if e["feedback_received"] is not None])
        
        # Calculate accuracy metrics
        correct_extractions = 0
        total_feedbacks = 0
        
        for extraction in self.extraction_history.values():
            if extraction["feedback_received"]:
                for term, is_correct in extraction["feedback_received"].items():
                    total_feedbacks += 1
                    if is_correct:
                        correct_extractions += 1
        
        return {
            "total_extractions": total_extractions,
            "extractions_with_feedback": feedback_received,
            "feedback_coverage": feedback_received / max(total_extractions, 1),
            "extraction_accuracy": correct_extractions / max(total_feedbacks, 1),
            "ready_for_rl_training": feedback_received >= 10  # Threshold for RL
        }