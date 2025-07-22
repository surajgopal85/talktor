# =============================================================================
# services/session/manager.py -  Updated with Database Persistence
# =============================================================================

import logging
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import and_

from models.database import (
    SessionLocal, Session, Transcription, Translation, 
    ExtractionAttempt, ExtractionCandidate, ExtractedMedication
)
from core.exceptions import DatabaseError

logger = logging.getLogger(__name__)

class SessionService:
    """Session management service with database persistence"""
    
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
    
    async def create_session(self, user_language: str = None, target_language: str = None, 
                           medical_context: str = "general") -> str:
        """Create a new session"""
        db = self._get_db()
        try:
            # Create new session record
            session = Session(
                user_language=user_language,
                target_language=target_language,
                medical_context=medical_context
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            logger.info(f"💾 Created new session: {session.id}")
            return session.id
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to create session: {e}")
            raise DatabaseError(f"Failed to create session: {e}")
        finally:
            self._close_db()
    
    async def store_transcription(self, session_id: str, transcription_result: Dict):
        """Store speech-to-text transcription"""
        db = self._get_db()
        try:
            # Ensure session exists
            session = db.query(Session).filter(Session.id == session_id).first()
            if not session:
                # Create session if it doesn't exist
                session = Session(id=session_id)
                db.add(session)
                db.commit()
                db.refresh(session)
            
            # Create transcription record
            transcription = Transcription(
                session_id=session_id,
                text=transcription_result["text"],
                language_detected=transcription_result.get("language"),
                confidence=transcription_result.get("confidence"),
                audio_duration=transcription_result.get("duration")
            )
            
            db.add(transcription)
            
            # Update session last activity
            session.last_activity = datetime.utcnow()
            
            db.commit()
            logger.info(f"💾 Stored transcription for session {session_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to store transcription: {e}")
            raise DatabaseError(f"Failed to store transcription: {e}")
        finally:
            self._close_db()
    
    async def store_medical_translation(self, session_id: str, request, translation_result: Dict,
                                      extraction_result: Dict, follow_up_questions: List[str]):
        """Store medical translation with extraction data"""
        db = self._get_db()
        try:
            # Ensure session exists
            session = db.query(Session).filter(Session.id == session_id).first()
            if not session:
                session = Session(
                    id=session_id,
                    user_language=request.source_language,
                    target_language=request.target_language,
                    medical_context=request.medical_context
                )
                db.add(session)
                db.commit()
                db.refresh(session)
            
            # Create translation record
            translation = Translation(
                session_id=session_id,
                original_text=request.text,
                translated_text=translation_result["standard_translation"],
                enhanced_translation=translation_result["enhanced_translation"],
                source_language=request.source_language,
                target_language=request.target_language,
                medical_context=request.medical_context,
                medical_accuracy_score=extraction_result["metadata"]["successful_extractions"] / max(extraction_result["metadata"]["total_candidates"], 1),
                follow_up_questions=follow_up_questions
            )
            
            db.add(translation)
            
            # Update session last activity
            session.last_activity = datetime.utcnow()
            
            db.commit()
            logger.info(f"💾 Stored medical translation for session {session_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to store medical translation: {e}")
            raise DatabaseError(f"Failed to store medical translation: {e}")
        finally:
            self._close_db()
    
    async def get_session(self, session_id: str) -> Dict:
        """Retrieve complete session data"""
        db = self._get_db()
        try:
            # Get session with all related data
            session = db.query(Session).filter(Session.id == session_id).first()
            
            if not session:
                raise DatabaseError("Session not found")
            
            # Build response with all session data
            session_data = {
                "session_id": session.id,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "last_activity": session.last_activity.isoformat() if session.last_activity else None,
                "user_language": session.user_language,
                "target_language": session.target_language,
                "medical_context": session.medical_context,
                "transcriptions": [
                    {
                        "id": t.id,
                        "text": t.text,
                        "language_detected": t.language_detected,
                        "confidence": t.confidence,
                        "created_at": t.created_at.isoformat() if t.created_at else None
                    } for t in session.transcriptions
                ],
                "translations": [
                    {
                        "id": t.id,
                        "original_text": t.original_text,
                        "translated_text": t.translated_text,
                        "enhanced_translation": t.enhanced_translation,
                        "medical_accuracy_score": t.medical_accuracy_score,
                        "follow_up_questions": t.follow_up_questions,
                        "created_at": t.created_at.isoformat() if t.created_at else None
                    } for t in session.translations
                ],
                "extractions": [
                    {
                        "id": e.id,
                        "original_text": e.original_text,
                        "total_candidates": e.total_candidates,
                        "successful_extractions": e.successful_extractions,
                        "learning_status": e.learning_status,
                        "created_at": e.created_at.isoformat() if e.created_at else None
                    } for e in session.extractions
                ]
            }
            
            logger.info(f"📖 Retrieved session {session_id} with {len(session.translations)} translations")
            return session_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get session: {e}")
            raise DatabaseError(f"Failed to get session: {e}")
        finally:
            self._close_db()
    
    async def delete_session(self, session_id: str):
        """Delete session and all related data for privacy compliance"""
        db = self._get_db()
        try:
            session = db.query(Session).filter(Session.id == session_id).first()
            
            if not session:
                raise DatabaseError("Session not found")
            
            # SQLAlchemy will cascade delete all related records
            db.delete(session)
            db.commit()
            
            logger.info(f"🗑️ Deleted session {session_id} and all related data")
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to delete session: {e}")
            raise DatabaseError(f"Failed to delete session: {e}")
        finally:
            self._close_db()
    
    async def get_session_analytics(self, session_id: str) -> Dict:
        """Get analytics for a specific session"""
        db = self._get_db()
        try:
            session = db.query(Session).filter(Session.id == session_id).first()
            
            if not session:
                raise DatabaseError("Session not found")
            
            # Calculate session analytics
            analytics = {
                "session_id": session.id,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "last_activity": session.last_activity.isoformat() if session.last_activity else None,
                "total_transcriptions": len(session.transcriptions),
                "total_translations": len(session.translations),
                "total_extractions": len(session.extractions),
                "medical_context": session.medical_context,
                "languages": {
                    "source": session.user_language,
                    "target": session.target_language
                },
                "extraction_stats": {
                    "pending_feedback": len([e for e in session.extractions if e.learning_status == "pending_feedback"]),
                    "with_feedback": len([e for e in session.extractions if e.learning_status == "feedback_received"])
                }
            }
            
            # Calculate average accuracy if translations exist
            if session.translations:
                accuracy_scores = [t.medical_accuracy_score for t in session.translations if t.medical_accuracy_score is not None]
                if accuracy_scores:
                    analytics["average_medical_accuracy"] = sum(accuracy_scores) / len(accuracy_scores)
            
            logger.info(f"📊 Generated analytics for session {session_id}")
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Failed to get session analytics: {e}")
            raise DatabaseError(f"Failed to get session analytics: {e}")
        finally:
            self._close_db()
    
    async def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """Get recent sessions for admin/analytics"""
        db = self._get_db()
        try:
            sessions = db.query(Session).order_by(Session.last_activity.desc()).limit(limit).all()
            
            return [
                {
                    "session_id": s.id,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "last_activity": s.last_activity.isoformat() if s.last_activity else None,
                    "medical_context": s.medical_context,
                    "interaction_count": len(s.transcriptions) + len(s.translations)
                } for s in sessions
            ]
            
        except Exception as e:
            logger.error(f"❌ Failed to get recent sessions: {e}")
            raise DatabaseError(f"Failed to get recent sessions: {e}")
        finally:
            self._close_db()
    
    async def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """Clean up sessions older than specified days"""
        db = self._get_db()
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Find old sessions
            old_sessions = db.query(Session).filter(
                Session.last_activity < cutoff_date
            ).all()
            
            count = len(old_sessions)
            
            # Delete old sessions (cascade will handle related records)
            for session in old_sessions:
                db.delete(session)
            
            db.commit()
            
            logger.info(f"🧹 Cleaned up {count} sessions older than {days_old} days")
            return count
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to cleanup old sessions: {e}")
            raise DatabaseError(f"Failed to cleanup old sessions: {e}")
        finally:
            self._close_db()