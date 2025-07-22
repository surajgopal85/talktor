# services/medical_intelligence/learning.py - Updated with Database Persistence

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import and_, func, desc

# Alternative (absolute imports):
from models.database import (
    SessionLocal, ExtractionAttempt, ExtractionCandidate, 
    ExtractedMedication, ExtractionFeedback, LearningMetrics
)
from core.exceptions import DatabaseError, LearningError

logger = logging.getLogger(__name__)

class LearningManager:
    """
    Manages learning data collection and reinforcement learning infrastructure
    Stores extraction attempts for future RL training with database persistence
    """
    
    def __init__(self):
        self.db_session = None
        
    def _get_db(self) -> DBSession:
        """Get database session"""
        if not self.db_session:
            self.db_session = SessionLocal()
        return self.db_session
    
    def _close_db(self):
        """Close database session"""
        if self.db_session:
            self.db_session.close()
            self.db_session = None
    
    async def store_extraction_attempt(self, session_id: str, text: str, candidates: List[Dict], 
                                     validated_medications: List[Dict], metadata: Dict) -> str:
        """Store extraction attempt for learning with full database persistence"""
        db = self._get_db()
        try:
            extraction_id = str(uuid.uuid4())
            
            # Create main extraction attempt record
            extraction_attempt = ExtractionAttempt(
                id=extraction_id,
                session_id=session_id,
                original_text=text,
                medical_context=metadata.get("medical_context", "general"),
                total_candidates=metadata["total_candidates"],
                successful_extractions=metadata["successful_extractions"],
                extraction_strategies_used=metadata["extraction_strategies_used"],
                confidence_threshold_used=metadata.get("confidence_threshold_used", 0.6),
                learning_status="pending_feedback"
            )
            
            db.add(extraction_attempt)
            db.flush()  # Get the ID without committing
            
            # Store extraction candidates
            for candidate in candidates:
                candidate_record = ExtractionCandidate(
                    extraction_id=extraction_id,
                    term=candidate["term"],
                    strategy=candidate["strategy"],
                    context=candidate["context"],
                    position=candidate["position"],
                    confidence_modifiers=candidate.get("confidence_modifiers", {})
                )
                db.add(candidate_record)
            
            # Store validated medications
            for med_result in validated_medications:
                medication = med_result["medication"]
                
                medication_record = ExtractedMedication(
                    extraction_id=extraction_id,
                    original_term=med_result["original_term"],
                    canonical_name=medication.get("canonical_name"),
                    rxcui=medication.get("rxcui"),
                    extraction_confidence=med_result["extraction_confidence"],
                    extraction_strategy=med_result["extraction_strategy"],
                    context=med_result["context"],
                    position=med_result["position"],
                    api_data=medication,  # Store full API response
                    brand_names=medication.get("brand_names", []),
                    indications=medication.get("indications", []),
                    contraindications=medication.get("contraindications", []),
                    pregnancy_category=medication.get("pregnancy_category")
                )
                db.add(medication_record)
            
            db.commit()
            
            logger.info(f"📚 Stored extraction attempt {extraction_id} with {len(candidates)} candidates and {len(validated_medications)} medications")
            return extraction_id
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to store extraction attempt: {e}")
            raise DatabaseError(f"Failed to store extraction attempt: {e}")
        finally:
            self._close_db()
    
    async def record_feedback(self, extraction_id: str, feedback: Dict[str, bool], 
                            feedback_type: str = "user", confidence: float = 1.0) -> Dict:
        """Record doctor/user feedback on extraction accuracy"""
        db = self._get_db()
        try:
            # Verify extraction exists
            extraction = db.query(ExtractionAttempt).filter(
                ExtractionAttempt.id == extraction_id
            ).first()
            
            if not extraction:
                raise LearningError("Extraction attempt not found")
            
            # Record feedback for each medication
            feedback_records = []
            for medication_term, is_correct in feedback.items():
                feedback_record = ExtractionFeedback(
                    extraction_id=extraction_id,
                    medication_term=medication_term,
                    is_correct=is_correct,
                    feedback_type=feedback_type,
                    confidence_in_feedback=confidence
                )
                db.add(feedback_record)
                feedback_records.append(feedback_record)
            
            # Update extraction status
            extraction.learning_status = "feedback_received"
            extraction.feedback_timestamp = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"📝 Recorded feedback for extraction {extraction_id}: {feedback}")
            
            # Calculate learning readiness
            await self._update_learning_metrics()
            
            return {
                "message": "Feedback recorded successfully",
                "extraction_id": extraction_id,
                "feedback": feedback,
                "feedback_records": len(feedback_records),
                "learning_status": "updated"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to record feedback: {e}")
            raise LearningError(f"Failed to record feedback: {e}")
        finally:
            self._close_db()
    
    async def get_learning_analytics(self, time_period_days: int = 30) -> Dict:
        """Get comprehensive learning analytics for reinforcement learning"""
        db = self._get_db()
        try:
            # Calculate time window
            cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)
            
            # Get extraction statistics
            total_extractions = db.query(ExtractionAttempt).filter(
                ExtractionAttempt.created_at >= cutoff_date
            ).count()
            
            extractions_with_feedback = db.query(ExtractionAttempt).filter(
                and_(
                    ExtractionAttempt.created_at >= cutoff_date,
                    ExtractionAttempt.learning_status == "feedback_received"
                )
            ).count()
            
            # Get feedback accuracy
            correct_feedback = db.query(ExtractionFeedback).join(ExtractionAttempt).filter(
                and_(
                    ExtractionAttempt.created_at >= cutoff_date,
                    ExtractionFeedback.is_correct == True
                )
            ).count()
            
            total_feedback = db.query(ExtractionFeedback).join(ExtractionAttempt).filter(
                ExtractionAttempt.created_at >= cutoff_date
            ).count()
            
            # Calculate average confidence
            avg_confidence_result = db.query(func.avg(ExtractedMedication.extraction_confidence)).join(ExtractionAttempt).filter(
                ExtractionAttempt.created_at >= cutoff_date
            ).scalar()
            
            avg_confidence = float(avg_confidence_result) if avg_confidence_result else 0.0
            
            # Strategy performance analysis
            strategy_performance = await self._analyze_strategy_performance(cutoff_date)
            
            # Learning readiness assessment
            ready_for_training = extractions_with_feedback >= 10  # Minimum threshold
            
            analytics = {
                "time_period_days": time_period_days,
                "total_extractions": total_extractions,
                "extractions_with_feedback": extractions_with_feedback,
                "feedback_coverage": extractions_with_feedback / max(total_extractions, 1),
                "extraction_accuracy": correct_feedback / max(total_feedback, 1),
                "average_confidence": avg_confidence,
                "strategy_performance": strategy_performance,
                "ready_for_rl_training": ready_for_training,
                "training_data_size": extractions_with_feedback,
                "feedback_quality": {
                    "total_feedback_items": total_feedback,
                    "positive_feedback": correct_feedback,
                    "negative_feedback": total_feedback - correct_feedback
                }
            }
            
            logger.info(f"📊 Generated learning analytics: {analytics['extraction_accuracy']:.2%} accuracy, {analytics['feedback_coverage']:.2%} coverage")
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Failed to get learning analytics: {e}")
            raise LearningError(f"Failed to get learning analytics: {e}")
        finally:
            self._close_db()
    
    async def _analyze_strategy_performance(self, cutoff_date: datetime) -> Dict:
        """Analyze performance of different extraction strategies"""
        db = self._get_db()
        try:
            strategy_stats = {}
            
            # Get all strategies used
            strategies = db.query(ExtractedMedication.extraction_strategy).join(ExtractionAttempt).filter(
                ExtractionAttempt.created_at >= cutoff_date
            ).distinct().all()
            
            for (strategy,) in strategies:
                if not strategy:
                    continue
                    
                # Get medications extracted with this strategy
                strategy_medications = db.query(ExtractedMedication).join(ExtractionAttempt).filter(
                    and_(
                        ExtractionAttempt.created_at >= cutoff_date,
                        ExtractedMedication.extraction_strategy == strategy
                    )
                ).all()
                
                # Calculate strategy performance
                total_extractions = len(strategy_medications)
                if total_extractions == 0:
                    continue
                
                # Get feedback for this strategy
                strategy_feedback = db.query(ExtractionFeedback).join(
                    ExtractedMedication, 
                    ExtractedMedication.original_term == ExtractionFeedback.medication_term
                ).join(ExtractionAttempt).filter(
                    and_(
                        ExtractionAttempt.created_at >= cutoff_date,
                        ExtractedMedication.extraction_strategy == strategy
                    )
                ).all()
                
                correct_feedback = len([f for f in strategy_feedback if f.is_correct])
                total_feedback = len(strategy_feedback)
                
                avg_confidence = sum(m.extraction_confidence for m in strategy_medications) / total_extractions
                
                strategy_stats[strategy] = {
                    "total_extractions": total_extractions,
                    "feedback_received": total_feedback,
                    "accuracy": correct_feedback / max(total_feedback, 1),
                    "average_confidence": avg_confidence,
                    "feedback_coverage": total_feedback / total_extractions
                }
            
            return strategy_stats
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze strategy performance: {e}")
            return {}
    
    async def get_extraction_candidates_for_training(self, limit: int = 100) -> List[Dict]:
        """Get extraction attempts ready for reinforcement learning training"""
        db = self._get_db()
        try:
            # Get extractions with feedback for training
            extractions = db.query(ExtractionAttempt).filter(
                ExtractionAttempt.learning_status == "feedback_received"
            ).order_by(desc(ExtractionAttempt.created_at)).limit(limit).all()
            
            training_data = []
            for extraction in extractions:
                # Get associated data
                candidates = db.query(ExtractionCandidate).filter(
                    ExtractionCandidate.extraction_id == extraction.id
                ).all()
                
                medications = db.query(ExtractedMedication).filter(
                    ExtractedMedication.extraction_id == extraction.id
                ).all()
                
                feedback = db.query(ExtractionFeedback).filter(
                    ExtractionFeedback.extraction_id == extraction.id
                ).all()
                
                # Structure training data
                training_entry = {
                    "extraction_id": extraction.id,
                    "original_text": extraction.original_text,
                    "candidates": [
                        {
                            "term": c.term,
                            "strategy": c.strategy,
                            "context": c.context,
                            "position": c.position,
                            "confidence_modifiers": c.confidence_modifiers
                        } for c in candidates
                    ],
                    "extracted_medications": [
                        {
                            "term": m.original_term,
                            "canonical_name": m.canonical_name,
                            "confidence": m.extraction_confidence,
                            "strategy": m.extraction_strategy
                        } for m in medications
                    ],
                    "feedback": {
                        f.medication_term: f.is_correct for f in feedback
                    },
                    "metadata": {
                        "total_candidates": extraction.total_candidates,
                        "successful_extractions": extraction.successful_extractions,
                        "strategies_used": extraction.extraction_strategies_used,
                        "confidence_threshold": extraction.confidence_threshold_used
                    }
                }
                
                training_data.append(training_entry)
            
            logger.info(f"🎯 Retrieved {len(training_data)} extraction attempts for RL training")
            return training_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get training candidates: {e}")
            raise LearningError(f"Failed to get training candidates: {e}")
        finally:
            self._close_db()
    
    async def _update_learning_metrics(self):
        """Update aggregated learning metrics for analytics dashboard"""
        db = self._get_db()
        try:
            # Calculate current metrics
            now = datetime.utcnow()
            week_ago = now - timedelta(days=7)
            
            # Get weekly statistics
            weekly_extractions = db.query(ExtractionAttempt).filter(
                ExtractionAttempt.created_at >= week_ago
            ).count()
            
            weekly_feedback = db.query(ExtractionAttempt).filter(
                and_(
                    ExtractionAttempt.created_at >= week_ago,
                    ExtractionAttempt.learning_status == "feedback_received"
                )
            ).count()
            
            # Calculate accuracy
            correct_feedback = db.query(ExtractionFeedback).join(ExtractionAttempt).filter(
                and_(
                    ExtractionAttempt.created_at >= week_ago,
                    ExtractionFeedback.is_correct == True
                )
            ).count()
            
            total_feedback_items = db.query(ExtractionFeedback).join(ExtractionAttempt).filter(
                ExtractionAttempt.created_at >= week_ago
            ).count()
            
            accuracy_rate = correct_feedback / max(total_feedback_items, 1)
            
            # Create metrics record
            metrics = LearningMetrics(
                period_start=week_ago,
                period_end=now,
                total_extractions=weekly_extractions,
                extractions_with_feedback=weekly_feedback,
                accuracy_rate=accuracy_rate,
                ready_for_training=weekly_feedback >= 10,
                training_data_size=weekly_feedback
            )
            
            db.add(metrics)
            db.commit()
            
            logger.info(f"📈 Updated learning metrics: {accuracy_rate:.2%} accuracy")
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to update learning metrics: {e}")
        finally:
            self._close_db()
    
    async def cleanup_old_extractions(self, days_old: int = 90) -> int:
        """Clean up old extraction data for privacy and storage management"""
        db = self._get_db()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Find old extractions
            old_extractions = db.query(ExtractionAttempt).filter(
                ExtractionAttempt.created_at < cutoff_date
            ).all()
            
            count = len(old_extractions)
            
            # Delete old extractions (cascade will handle related records)
            for extraction in old_extractions:
                db.delete(extraction)
            
            db.commit()
            
            logger.info(f"🧹 Cleaned up {count} extraction attempts older than {days_old} days")
            return count
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to cleanup old extractions: {e}")
            raise LearningError(f"Failed to cleanup old extractions: {e}")
        finally:
            self._close_db()