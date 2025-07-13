# =============================================================================
# services/session/storage.py
# =============================================================================

import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SessionStorage:
    """
    Session storage abstraction
    In production: replace with Redis, PostgreSQL, or other persistent storage
    """
    
    def __init__(self):
        # In-memory storage for development
        self.sessions = {}
    
    async def store_session_data(self, session_id: str, data: Dict):
        """Store data for a session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "created_at": datetime.now().isoformat(),
                "interactions": []
            }
        
        self.sessions[session_id]["interactions"].append(data)
        self.sessions[session_id]["last_activity"] = datetime.now().isoformat()
        
        logger.info(f"💾 Stored session data for {session_id}")
    
    async def get_session_data(self, session_id: str) -> Optional[Dict]:
        """Retrieve session data"""
        return self.sessions.get(session_id)
    
    async def delete_session_data(self, session_id: str):
        """Delete session data"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"🗑️ Deleted session {session_id}")
        else:
            raise Exception("Session not found")
    
    async def get_all_sessions(self) -> Dict:
        """Get all sessions (for admin/analytics)"""
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": len([s for s in self.sessions.values() 
                                  if self._is_recent_activity(s.get("last_activity"))])
        }
    
    def _is_recent_activity(self, last_activity: str, hours: int = 24) -> bool:
        """Check if session had recent activity"""
        if not last_activity:
            return False
        
        try:
            from datetime import datetime, timedelta
            last_time = datetime.fromisoformat(last_activity)
            return datetime.now() - last_time < timedelta(hours=hours)
        except:
            return False