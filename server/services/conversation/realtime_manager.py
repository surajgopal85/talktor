# =============================================================================
# File 1: services/conversation/realtime_manager.py
# =============================================================================

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from fastapi import WebSocket, WebSocketDisconnect

# add for FE compatibility
import base64

# Import existing services
from ..translation.translator import TranslationService
from ..medical_intelligence import MedicalIntelligenceService
from ..audio.whisper_service import WhisperService  # ✅ Use existing


logger = logging.getLogger(__name__)

# Placeholder TTS service only (since you might not have this one yet)
class TTSService:
    async def synthesize_speech(self, text: str, language: str = "en") -> Dict:
        return {
            "audio_data": "dGVzdF9hdWRpb19kYXRh",  # placeholder for now
            "format": "wav"
        }

class SpeakerRole(Enum):
    DOCTOR = "doctor"
    PATIENT = "patient"
    SYSTEM = "system"

class MessageType(Enum):
    AUDIO_CHUNK = "audio_chunk"
    TRANSCRIPTION = "transcription"
    TRANSLATION = "translation"
    MEDICAL_ALERT = "medical_alert"
    CONVERSATION_SUMMARY = "conversation_summary"
    TTS_AUDIO = "tts_audio"
    SYSTEM_STATUS = "system_status"
    ERROR = "error"

@dataclass
class ConversationMessage:
    id: str
    session_id: str
    speaker: SpeakerRole
    message_type: MessageType
    content: Any
    timestamp: datetime
    language: str
    metadata: Dict = None
    
    def to_dict(self):
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'speaker': self.speaker.value,
            'message_type': self.message_type.value
        }

@dataclass
class ConversationSession:
    session_id: str
    doctor_language: str
    patient_language: str
    active_speaker: Optional[SpeakerRole]
    messages: List[ConversationMessage]
    medical_context: Dict
    safety_alerts: List[Dict]
    created_at: datetime
    last_activity: datetime
    
    def add_message(self, message: ConversationMessage):
        self.messages.append(message)
        self.last_activity = datetime.now()

class RealTimeConversationManager:
    """
    Manages real-time medical conversations with seamless translation
    Handles WebSocket connections, audio streaming, and medical intelligence
    """
    
    def __init__(self):
        # Initialize services
        self.translation_service = TranslationService()
        self.medical_service = MedicalIntelligenceService()
        self.whisper_service = WhisperService()
        self.tts_service = TTSService()
        
        # Active connections and sessions
        self.active_connections: Dict[str, WebSocket] = {}
        self.active_sessions: Dict[str, ConversationSession] = {}
        
        # Configuration
        self.config = {
            "audio_chunk_size": 1024,
            "transcription_timeout": 5.0,
            "medical_alert_priority": "immediate",
            "auto_tts_enabled": True,
            "conversation_timeout": 3600  # 1 hour
        }
    
    async def create_conversation_session(self, doctor_lang: str = "en", 
                                        patient_lang: str = "es") -> str:
        """Create a new conversation session"""
        session_id = str(uuid.uuid4())
        
        session = ConversationSession(
            session_id=session_id,
            doctor_language=doctor_lang,
            patient_language=patient_lang,
            active_speaker=None,
            messages=[],
            medical_context={"specialty": "general", "detected_conditions": []},
            safety_alerts=[],
            created_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        self.active_sessions[session_id] = session
        
        logger.info(f"🏥 Created conversation session {session_id}: {doctor_lang} ↔ {patient_lang}")
        return session_id
    
    async def connect_websocket(self, websocket: WebSocket, session_id: str, 
                              role: str) -> bool:
        """Connect WebSocket client to conversation session"""
        try:
            await websocket.accept()
            
            # Validate session exists
            if session_id not in self.active_sessions:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Session {session_id} not found"
                })
                await websocket.close()
                return False
            
            # Store connection
            connection_id = f"{session_id}_{role}"
            self.active_connections[connection_id] = websocket
            
            # Send welcome message
            welcome_message = ConversationMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                speaker=SpeakerRole.SYSTEM,
                message_type=MessageType.SYSTEM_STATUS,
                content={
                    "status": "connected",
                    "role": role,
                    "session_id": session_id,
                    "capabilities": ["audio_streaming", "real_time_translation", "medical_intelligence"]
                },
                timestamp=datetime.now(),
                language="en"
            )
            
            await websocket.send_json(welcome_message.to_dict())
            
            logger.info(f"✅ WebSocket connected: {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed: {e}")
            return False
    
    async def handle_websocket_message(self, websocket: WebSocket, session_id: str, 
                                     role: str, data: Dict):
        """Handle incoming WebSocket message"""
        try:
            message_type = MessageType(data.get("type"))
            
            if message_type == MessageType.AUDIO_CHUNK:
                await self._handle_audio_chunk(websocket, session_id, role, data)
            
            elif message_type == MessageType.TRANSCRIPTION:
                await self._handle_transcription(websocket, session_id, role, data)
            
            else:
                logger.warning(f"⚠️ Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"❌ Error handling WebSocket message: {e}")
            await self._send_error(websocket, str(e))
    
    async def _handle_audio_chunk(self, websocket: WebSocket, session_id: str, 
                                role: str, data: Dict):
        """Handle incoming audio chunk for transcription"""
        try:
            # Get audio data
            audio_data = data.get("audio_data")  # Base64 encoded audio
            speaker_role = SpeakerRole(role)
            
            # Get session and determine source language
            session = self.active_sessions[session_id]
            source_lang = (session.doctor_language if speaker_role == SpeakerRole.DOCTOR 
                          else session.patient_language)
            
            # Fixed - decode base64 audio data first:
            try:
                audio_bytes = base64.b64decode(audio_data)
                transcription_result = await self.whisper_service.transcribe_audio(audio_bytes)
            except Exception as decode_error:
                logger.error(f"Audio decoding failed: {decode_error}")
                transcription_result = {"text": "", "confidence": 0.0}
            
            if transcription_result.get("text"):
                # Create transcription message
                transcription_msg = ConversationMessage(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    speaker=speaker_role,
                    message_type=MessageType.TRANSCRIPTION,
                    content={
                        "text": transcription_result["text"],
                        "confidence": transcription_result.get("confidence", 0.0),
                        "language": source_lang
                    },
                    timestamp=datetime.now(),
                    language=source_lang
                )
                
                session.add_message(transcription_msg)
                
                # Broadcast transcription to all clients
                await self._broadcast_to_session(session_id, transcription_msg)
                
                # Process for translation and medical intelligence
                await self._process_conversation_turn(session_id, transcription_msg)
                
        except Exception as e:
            logger.error(f"❌ Audio processing failed: {e}")
            await self._send_error(websocket, f"Audio processing failed: {str(e)}")

    async def _handle_transcription(self, websocket: WebSocket, session_id: str, role: str, data: Dict):
        """Handle incoming transcription directly (bypass audio processing)"""
        try:
            # Get transcription data
            text = data.get("text")
            language = data.get("language", "en")
            speaker_role = SpeakerRole(role)
            
            if text:
                # Create transcription message
                transcription_msg = ConversationMessage(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    speaker=speaker_role,
                    message_type=MessageType.TRANSCRIPTION,
                    content={
                        "text": text,
                        "confidence": 0.95,  # High confidence for direct text input
                        "language": language
                    },
                    timestamp=datetime.now(),
                    language=language
                )
                
                session = self.active_sessions[session_id]
                session.add_message(transcription_msg)
                
                # Broadcast transcription to all clients
                await self._broadcast_to_session(session_id, transcription_msg)
                
                # Process for translation and medical intelligence
                await self._process_conversation_turn(session_id, transcription_msg)
            
        except Exception as e:
            logger.error(f"❌ Transcription processing failed: {e}")
            await self._send_error(websocket, f"Transcription processing failed: {str(e)}")
    
    async def _process_conversation_turn(self, session_id: str, 
                                       transcription_msg: ConversationMessage):
        """Process a complete conversation turn with translation and medical intelligence"""
        try:
            session = self.active_sessions[session_id]
            speaker_role = transcription_msg.speaker
            text = transcription_msg.content["text"]
            source_lang = transcription_msg.language
            
            # Determine target language
            target_lang = (session.patient_language if speaker_role == SpeakerRole.DOCTOR 
                          else session.doctor_language)
            
            # 1. Medical Intelligence Processing
            medical_result = await self.medical_service.process_medical_text(
                text, session_id, "general"  # Could auto-detect specialty
            )
            
            # 2. Check for safety alerts
            await self._check_safety_alerts(session_id, medical_result)
            
            # 3. Translation with medical context
            translation_result = await self.translation_service.translate_with_medical_context(
                text, source_lang, target_lang, medical_result.get("medications", [])
            )
            
            # 4. Create translation message
            translation_msg = ConversationMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                speaker=speaker_role,
                message_type=MessageType.TRANSLATION,
                content={
                    "original_text": text,
                    "translated_text": translation_result["enhanced_translation"],
                    "source_language": source_lang,
                    "target_language": target_lang,
                    "medical_context": medical_result.get("medications", []),
                    "confidence": translation_result.get("confidence", 0.95)
                },
                timestamp=datetime.now(),
                language=target_lang,
                metadata={"medical_intelligence": medical_result}
            )
            
            session.add_message(translation_msg)
            
            # 5. Broadcast translation
            await self._broadcast_to_session(session_id, translation_msg)
            
            # 6. Generate TTS if enabled
            if self.config["auto_tts_enabled"]:
                await self._generate_and_send_tts(session_id, translation_msg)
            
            # 7. Update conversation summary
            await self._update_conversation_summary(session_id)
            
        except Exception as e:
            logger.error(f"❌ Conversation processing failed: {e}")
    
    async def _check_safety_alerts(self, session_id: str, medical_result: Dict):
        """Check for medical safety alerts and broadcast if urgent"""
        try:
            session = self.active_sessions[session_id]
            
            # Extract safety alerts from medical result
            medical_notes = medical_result.get("medical_notes", [])
            urgent_alerts = [note for note in medical_notes 
                           if note.get("importance") == "urgent"]
            
            for alert in urgent_alerts:
                # Create safety alert message
                alert_msg = ConversationMessage(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    speaker=SpeakerRole.SYSTEM,
                    message_type=MessageType.MEDICAL_ALERT,
                    content={
                        "alert_type": alert.get("type", "safety_alert"),
                        "message": alert.get("message"),
                        "severity": "urgent",
                        "action_required": True
                    },
                    timestamp=datetime.now(),
                    language="en"  # System alerts in English
                )
                
                session.add_message(alert_msg)
                session.safety_alerts.append(alert)
                
                # Immediate broadcast for urgent alerts
                await self._broadcast_to_session(session_id, alert_msg)
                
                logger.warning(f"🚨 URGENT MEDICAL ALERT: {alert.get('message')}")
                
        except Exception as e:
            logger.error(f"❌ Safety alert check failed: {e}")
    
    async def _generate_and_send_tts(self, session_id: str, translation_msg: ConversationMessage):
        """Generate TTS audio for translation and send to appropriate clients"""
        try:
            translated_text = translation_msg.content["translated_text"]
            target_language = translation_msg.content["target_language"]
            
            # Generate TTS audio
            tts_result = await self.tts_service.synthesize_speech(
                translated_text, language=target_language
            )
            
            if tts_result.get("audio_data"):
                # Create TTS message
                tts_msg = ConversationMessage(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    speaker=translation_msg.speaker,
                    message_type=MessageType.TTS_AUDIO,
                    content={
                        "audio_data": tts_result["audio_data"],  # Base64 encoded
                        "text": translated_text,
                        "language": target_language,
                        "format": tts_result.get("format", "wav")
                    },
                    timestamp=datetime.now(),
                    language=target_language
                )
                
                # Broadcast TTS to session
                await self._broadcast_to_session(session_id, tts_msg)
                
        except Exception as e:
            logger.error(f"❌ TTS generation failed: {e}")
    
    async def _update_conversation_summary(self, session_id: str):
        """Update real-time conversation summary"""
        try:
            session = self.active_sessions[session_id]
            
            # Extract recent conversation content
            recent_messages = session.messages[-10:]  # Last 10 messages
            conversation_text = " ".join([
                msg.content.get("text", "") for msg in recent_messages 
                if msg.message_type == MessageType.TRANSCRIPTION
            ])
            
            if conversation_text:
                # Generate summary with medical intelligence
                summary_result = await self.medical_service.process_medical_text(
                    conversation_text, session_id, "general"
                )
                
                # Create summary message
                summary_msg = ConversationMessage(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    speaker=SpeakerRole.SYSTEM,
                    message_type=MessageType.CONVERSATION_SUMMARY,
                    content={
                        "medications_discussed": summary_result.get("medications", []),
                        "medical_context": summary_result.get("medical_context", {}),
                        "follow_up_questions": summary_result.get("follow_up_questions", []),
                        "safety_alerts_count": len(session.safety_alerts),
                        "last_updated": datetime.now().isoformat()
                    },
                    timestamp=datetime.now(),
                    language="en"
                )
                
                # Broadcast summary update
                await self._broadcast_to_session(session_id, summary_msg)
                
        except Exception as e:
            logger.error(f"❌ Summary update failed: {e}")
    
    async def _broadcast_to_session(self, session_id: str, message: ConversationMessage):
        """Broadcast message to all connections in a session"""
        try:
            # Find all connections for this session
            session_connections = {
                conn_id: websocket for conn_id, websocket in self.active_connections.items()
                if conn_id.startswith(session_id)
            }
            
            # Send to all connections
            for conn_id, websocket in session_connections.items():
                try:
                    await websocket.send_json(message.to_dict())
                except Exception as e:
                    logger.warning(f"⚠️ Failed to send to {conn_id}: {e}")
                    # Remove dead connection
                    self.active_connections.pop(conn_id, None)
                    
        except Exception as e:
            logger.error(f"❌ Broadcast failed: {e}")
    
    async def _send_error(self, websocket: WebSocket, error_message: str):
        """Send error message to WebSocket client"""
        try:
            error_msg = {
                "type": "error",
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_json(error_msg)
        except Exception as e:
            logger.error(f"❌ Error sending error message: {e}")
    
    async def disconnect_websocket(self, session_id: str, role: str):
        """Handle WebSocket disconnection"""
        connection_id = f"{session_id}_{role}"
        self.active_connections.pop(connection_id, None)
        logger.info(f"🔌 WebSocket disconnected: {connection_id}")
    
    async def end_conversation_session(self, session_id: str) -> Dict:
        """End conversation session and generate final summary"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return {"error": "Session not found"}
            
            # Generate final summary
            final_summary = await self._generate_final_summary(session)
            
            # Clean up connections
            session_connections = [
                conn_id for conn_id in self.active_connections.keys()
                if conn_id.startswith(session_id)
            ]
            
            for conn_id in session_connections:
                self.active_connections.pop(conn_id, None)
            
            # Remove session
            self.active_sessions.pop(session_id, None)
            
            logger.info(f"🏁 Conversation session ended: {session_id}")
            return final_summary
            
        except Exception as e:
            logger.error(f"❌ Session end failed: {e}")
            return {"error": str(e)}
    
    async def _generate_final_summary(self, session: ConversationSession) -> Dict:
        """Generate comprehensive final conversation summary"""
        try:
            # Extract all conversation text
            conversation_text = " ".join([
                msg.content.get("text", "") for msg in session.messages 
                if msg.message_type == MessageType.TRANSCRIPTION
            ])
            
            # Get comprehensive medical analysis
            final_analysis = await self.medical_service.process_medical_text(
                conversation_text, session.session_id, "general"
            )
            
            # Count message statistics
            doctor_messages = len([m for m in session.messages if m.speaker == SpeakerRole.DOCTOR])
            patient_messages = len([m for m in session.messages if m.speaker == SpeakerRole.PATIENT])
            
            return {
                "session_id": session.session_id,
                "duration_minutes": (session.last_activity - session.created_at).total_seconds() / 60,
                "message_count": {
                    "doctor": doctor_messages,
                    "patient": patient_messages,
                    "total": len(session.messages)
                },
                "medical_summary": {
                    "medications_discussed": final_analysis.get("medications", []),
                    "medical_context": final_analysis.get("medical_context", {}),
                    "safety_alerts": session.safety_alerts,
                    "follow_up_recommendations": final_analysis.get("follow_up_questions", [])
                },
                "languages": {
                    "doctor": session.doctor_language,
                    "patient": session.patient_language
                },
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Final summary generation failed: {e}")
            return {"error": "Summary generation failed"}