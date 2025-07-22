# =============================================================================
# routers/conversation_router.py - FIXED IMPORTS
# =============================================================================

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

# FIXED: Import the RealTimeConversationManager
from services.conversation.realtime_manager import RealTimeConversationManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversation", tags=["Real-Time Conversation"])

# Global conversation manager instance
conversation_manager = RealTimeConversationManager()

class CreateSessionRequest(BaseModel):
    doctor_language: str = "en"
    patient_language: str = "es"
    medical_specialty: Optional[str] = "general"

class EndSessionRequest(BaseModel):
    session_id: str

@router.post("/create")
async def create_conversation_session(request: CreateSessionRequest):
    """Create a new real-time conversation session"""
    try:
        session_id = await conversation_manager.create_conversation_session(
            request.doctor_language, request.patient_language
        )
        
        return {
            "session_id": session_id,
            "doctor_language": request.doctor_language,
            "patient_language": request.patient_language,
            "websocket_urls": {
                "doctor": f"/conversation/ws/{session_id}/doctor",
                "patient": f"/conversation/ws/{session_id}/patient"
            },
            "status": "ready"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/{session_id}/{role}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, role: str):
    """WebSocket endpoint for real-time conversation"""
    
    # Validate role
    if role not in ["doctor", "patient"]:
        await websocket.close(code=400, reason="Invalid role")
        return
    
    # Connect to session
    connected = await conversation_manager.connect_websocket(websocket, session_id, role)
    if not connected:
        return
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Handle the message
            await conversation_manager.handle_websocket_message(
                websocket, session_id, role, data
            )
            
    except WebSocketDisconnect:
        await conversation_manager.disconnect_websocket(session_id, role)
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        await conversation_manager.disconnect_websocket(session_id, role)

@router.post("/end")
async def end_conversation_session(request: EndSessionRequest):
    """End conversation session and get final summary"""
    try:
        summary = await conversation_manager.end_conversation_session(request.session_id)
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active")
async def get_active_sessions():
    """Get list of active conversation sessions"""
    try:
        sessions = []
        for session_id, session in conversation_manager.active_sessions.items():
            sessions.append({
                "session_id": session_id,
                "doctor_language": session.doctor_language,
                "patient_language": session.patient_language,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "message_count": len(session.messages),
                "safety_alerts": len(session.safety_alerts)
            })
        
        return {"active_sessions": sessions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))