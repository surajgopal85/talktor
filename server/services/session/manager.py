# =============================================================================
# services/session/manager.py  
# =============================================================================

import logging
from typing import Dict, List, Optional
from datetime import datetime

from .storage import SessionStorage

logger = logging.getLogger(__name__)

class SessionService:
    """Session management service"""
    
    def __init__(self):
        self.storage = SessionStorage()
    
    async def store_transcription(self, session_id: str, transcription_result: Dict):
        """Store speech-to-text transcription"""
        await self.storage.store_session_data(session_id, {
            "type": "transcription",
            "timestamp": datetime.now().isoformat(),
            "text": transcription_result["text"],
            "language": transcription_result.get("language"),
            "confidence": transcription_result.get("confidence")
        })
    
    async def store_medical_translation(self, session_id: str, request, translation_result: Dict,
                                      extraction_result: Dict, follow_up_questions: List[str]):
        """Store medical translation with extraction data"""
        
        # Store translation data
        await self.storage.store_session_data(session_id, {
            "type": "medical_translation",
            "timestamp": datetime.now().isoformat(),
            "original_text": request.text,
            "standard_translation": translation_result["standard_translation"],
            "enhanced_translation": translation_result["enhanced_translation"],
            "follow_up_questions": follow_up_questions,
            "source_language": request.source_language,
            "target_language": request.target_language,
            "medical_context": request.medical_context,
            "extraction_metadata": extraction_result["metadata"]
        })
    
    async def get_session(self, session_id: str) -> Dict:
        """Retrieve session data"""
        return await self.storage.get_session_data(session_id)
    
    async def delete_session(self, session_id: str):
        """Delete session for privacy compliance"""
        await self.storage.delete_session_data(session_id)
    
    async def get_session_analytics(self, session_id: str) -> Dict:
        """Get analytics for a specific session"""
        session_data = await self.storage.get_session_data(session_id)
        
        if not session_data:
            raise Exception("Session not found")
        
        return {
            "session_id": session_id,
            "total_interactions": len(session_data.get("interactions", [])),
            "created_at": session_data.get("created_at"),
            "last_activity": session_data.get("last_activity")
        }