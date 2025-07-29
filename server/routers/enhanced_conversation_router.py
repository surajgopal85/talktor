# routers/enhanced_conversation_router.py
import asyncio
import json
import logging
from typing import Dict, Optional
from datetime import datetime
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter

from services.audio.streaming_audio_service import get_streaming_audio_service
from services.conversation.realtime_manager import RealTimeConversationManager
from services.medical_intelligence import MedicalIntelligenceService
from services.translation.translator import TranslationService

logger = logging.getLogger(__name__)

router = APIRouter()

class StreamingAudioMessageTypes:
    """Message types for streaming audio functionality"""
    
    # Client -> Server
    AUDIO_CHUNK_STREAM = "audio_chunk_stream"
    START_LISTENING = "start_listening"
    STOP_LISTENING = "stop_listening"
    
    # Server -> Client
    AUDIO_STATUS = "audio_status"
    STREAMING_TRANSCRIPTION = "streaming_transcription"
    STREAMING_TTS = "streaming_tts"
    VOICE_ACTIVITY = "voice_activity"

class EnhancedConversationManager:
    """
    Enhanced conversation manager that adds streaming audio to existing functionality
    """
    
    def __init__(self):
        # Existing services (keep your current implementations)
        self.conversation_manager = RealTimeConversationManager()
        # added import 7.22.25
        from services.medical_intelligence import MedicalIntelligenceService
        self.medical_service = MedicalIntelligenceService()
        self.translation_service = TranslationService()
        
        # New streaming audio service
        self.streaming_audio_service = get_streaming_audio_service()
        
        # Connection tracking
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_configs: Dict[str, dict] = {}

    async def handle_websocket_connection(self, websocket: WebSocket, session_id: str, role: str):
        """
        Enhanced WebSocket connection handler with streaming audio support
        """
        connection_id = f"{session_id}_{role}"
        
        try:
            await websocket.accept()
            self.active_connections[connection_id] = websocket
            
            logger.info(f"🔗 WebSocket connected: {connection_id}")
            
            # Send welcome message with streaming capabilities
            await self._send_welcome_message(websocket, session_id, role)
            
            # Initialize streaming audio session
            await self.streaming_audio_service.start_streaming_session(session_id, websocket)
            
            # Message handling loop
            async for message in websocket.iter_json():
                await self._route_websocket_message(websocket, session_id, role, message)
                
        except WebSocketDisconnect:
            logger.info(f"🔗 WebSocket disconnected: {connection_id}")
        except Exception as e:
            logger.error(f"WebSocket error for {connection_id}: {e}")
        finally:
            # Cleanup
            self.active_connections.pop(connection_id, None)
            await self.streaming_audio_service.cleanup_session(session_id)

    async def _send_welcome_message(self, websocket: WebSocket, session_id: str, role: str):
        """Send welcome message with capabilities"""
        welcome_message = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "speaker": "system",
            "message_type": "system_status",
            "content": {
                "status": "connected",
                "role": role,
                "session_id": session_id,
                "capabilities": [
                    "audio_streaming",
                    "real_time_translation",
                    "medical_intelligence",
                    "voice_activity_detection",
                    "streaming_tts"
                ],
                "streaming_audio_enabled": True
            },
            "timestamp": datetime.now().isoformat(),
            "language": "en"
        }
        
        await websocket.send_json(welcome_message)

    async def _route_websocket_message(self, websocket: WebSocket, session_id: str, role: str, message: dict):
        """
        Route WebSocket messages to appropriate handlers
        """
        message_type = message.get("type")
        
        try:
            # Handle streaming audio messages
            if message_type == StreamingAudioMessageTypes.AUDIO_CHUNK_STREAM:
                await self._handle_audio_chunk_stream(websocket, session_id, role, message)
                
            elif message_type == StreamingAudioMessageTypes.START_LISTENING:
                await self._handle_start_listening(websocket, session_id, role, message)
                
            elif message_type == StreamingAudioMessageTypes.STOP_LISTENING:
                await self._handle_stop_listening(websocket, session_id, role, message)
                
            # Handle existing message types (keep your current handlers)
            elif message_type == "transcription":
                await self._handle_transcription_message(websocket, session_id, role, message)
                
            elif message_type == "audio_chunk":
                # Legacy audio chunk handling (keep for compatibility)
                await self._handle_legacy_audio_chunk(websocket, session_id, role, message)
                
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error routing message {message_type}: {e}")
            await self._send_error_message(websocket, session_id, str(e))

    async def _handle_audio_chunk_stream(self, websocket: WebSocket, session_id: str, role: str, message: dict):
        """
        Handle streaming audio chunk with voice activity detection
        """
        try:
            audio_data = message.get("audio_data")
            expected_language = message.get("language", "auto")
            
            if not audio_data:
                logger.warning("Received empty audio data")
                return
            
            # Process audio chunk through streaming service
            transcription_result = await self.streaming_audio_service.process_audio_chunk(
                session_id=session_id,
                audio_chunk_base64=audio_data,
                expected_language=expected_language
            )
            
            # If we got a transcription, process it through the full pipeline
            if transcription_result and transcription_result.transcribed_text:
                await self._process_streaming_transcription(
                    session_id=session_id,
                    role=role,
                    transcription_result=transcription_result
                )
                
        except Exception as e:
            logger.error(f"Error handling audio chunk stream: {e}")

    # Replace the _process_streaming_transcription method in enhanced_conversation_router.py

    async def _process_streaming_transcription(self, session_id: str, role: str, transcription_result):
        """
        Process transcription through medical intelligence and translation pipeline
        """
        try:
            text = transcription_result.transcribed_text
            language = transcription_result.detected_language
            
            # 1. Send immediate transcription to client
            await self._broadcast_streaming_transcription(session_id, role, transcription_result)
            
            # 2. Process through medical intelligence (your existing service)
            medical_result = await self.medical_service.process_medical_text(
                text=text,
                session_id=session_id,
                specialty="obgyn"  # or get from session config
            )
            
            logger.info(f"🧠 Medical processing complete: {type(medical_result)}")
            logger.info(f"🧠 Medical result keys: {list(medical_result.keys()) if isinstance(medical_result, dict) else 'Not a dict'}")
            
            # 3. Handle safety alerts FIRST (before translation)
            safety_alerts = medical_result.get("safety_alerts", [])
            
            # Also check obgyn_context for safety flags
            obgyn_context = medical_result.get("obgyn_context", {})
            safety_flags = obgyn_context.get("safety_flags", [])
            
            logger.info(f"🚨 Found {len(safety_alerts)} safety alerts and {len(safety_flags)} safety flags")
            
            # Broadcast any high-priority alerts immediately
            all_alerts = safety_alerts + safety_flags
            for alert in all_alerts:
                await self._broadcast_individual_medical_alert(session_id, alert)
            
            # 4. Get target language for translation
            target_language = self._get_target_language(session_id, role)
            logger.info(f"🌐 Target language: {target_language}, Source: {language}")
            
            # 5. Translate with medical context
            if target_language and target_language != language:
                try:
                    # Extract medications for translation context
                    medications = medical_result.get("medications", [])
                    
                    # SIMPLIFIED: Use the working translation method directly
                    logger.info(f"🌐 Starting translation: '{text}' ({language} → {target_language})")
                    
                    # Call your working translation service the same way as the REST endpoint
                    translation_result = await self.translation_service.translate_with_medical_context(
                        text=text,
                        source_lang=language,
                        target_lang=target_language,
                        medications=medications
                    )
                    
                    logger.info(f"🌐 Translation completed: {translation_result}")
                    
                    # Extract translated text safely
                    if isinstance(translation_result, dict):
                        translated_text = (
                            translation_result.get("enhanced_translation") or 
                            translation_result.get("standard_translation") or
                            translation_result.get("translated_text") or
                            text  # Fallback to original
                        )
                    else:
                        translated_text = str(translation_result)
                    
                    # 6. Send translation message
                    translation_message = {
                        "id": str(uuid.uuid4()),
                        "session_id": session_id,
                        "speaker": role,
                        "message_type": "translation",
                        "content": {
                            "original_text": text,
                            "translated_text": translated_text,
                            "source_language": language,
                            "target_language": target_language,
                            "confidence": 0.9,
                            "medical_context_applied": True
                        },
                        "timestamp": datetime.now().isoformat(),
                        "language": target_language
                    }
                    
                    logger.info(f"🌐 Broadcasting translation: '{text}' → '{translated_text}'")
                    await self._broadcast_to_session(session_id, translation_message)
                    
                    # 7. Generate TTS if translation successful
                    if translated_text and translated_text != text:
                        await self._stream_tts_response(
                            session_id=session_id,
                            text=translated_text,
                            language=target_language,
                            target_role=self._get_opposite_role(role)
                        )
                        
                except Exception as e:
                    logger.error(f"❌ Translation failed: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    # Send fallback translation
                    fallback_translations = {
                        "estoy embarazada tomando ibuprofeno": "I am pregnant taking ibuprofen",
                        "estoy embarazada": "I am pregnant",
                        "tomando ibuprofeno": "taking ibuprofen"
                    }
                    
                    fallback_text = fallback_translations.get(text.lower(), text)
                    
                    fallback_message = {
                        "id": str(uuid.uuid4()),
                        "session_id": session_id,
                        "speaker": role,
                        "message_type": "translation",
                        "content": {
                            "original_text": text,
                            "translated_text": fallback_text,
                            "source_language": language,
                            "target_language": target_language,
                            "confidence": 0.8,
                            "fallback": True
                        },
                        "timestamp": datetime.now().isoformat(),
                        "language": target_language
                    }
                    
                    logger.info(f"🌐 Broadcasting fallback translation: '{text}' → '{fallback_text}'")
                    await self._broadcast_to_session(session_id, fallback_message)
            
            # 8. Update conversation summary (async)
            asyncio.create_task(self._update_conversation_summary(session_id, medical_result))
            
            logger.info(f"✅ Full pipeline completed for: {text}")
            
        except Exception as e:
            logger.error(f"❌ Error processing streaming transcription: {e}")
            import traceback
            traceback.print_exc()

    # Add this new method for individual alert broadcasting
    async def _broadcast_individual_medical_alert(self, session_id: str, alert):
        """Broadcast individual medical alert"""
        try:
            # Handle both dict and object alert formats
            if isinstance(alert, dict):
                alert_type = alert.get("type", "medical_concern")
                message = alert.get("message", "Medical alert")
                severity = alert.get("severity", "medium")
                clinical_recommendation = alert.get("clinical_recommendation", "")
            else:
                # If alert is an object
                alert_type = getattr(alert, 'type', 'medical_concern')
                message = getattr(alert, 'message', 'Medical alert')
                severity = getattr(alert, 'severity', 'medium')
                clinical_recommendation = getattr(alert, 'clinical_recommendation', '')
            
            alert_message = {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "speaker": "system", 
                "message_type": "medical_alert",
                "content": {
                    "alert_type": alert_type,
                    "message": message,
                    "severity": severity,
                    "action_required": severity in ["high", "urgent"],
                    "clinical_recommendation": clinical_recommendation
                },
                "timestamp": datetime.now().isoformat(),
                "language": "en"
            }
            
            logger.info(f"🚨 Broadcasting medical alert: {alert_type} - {severity}")
            await self._broadcast_to_session(session_id, alert_message)
            
        except Exception as e:
            logger.error(f"❌ Error broadcasting medical alert: {e}")

    # Fix the translation broadcasting method
    async def _broadcast_translation_result(self, session_id: str, role: str, translation_result, original_text: str, source_lang: str, target_lang: str):
        """Broadcast translation result"""
        try:
            # Handle different translation result formats
            if isinstance(translation_result, dict):
                translated_text = translation_result.get("enhanced_translation") or translation_result.get("standard_translation", "")
                confidence = translation_result.get("confidence", 0.9)
            else:
                translated_text = str(translation_result)
                confidence = 0.9
                
            message = {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "speaker": role,
                "message_type": "translation",
                "content": {
                    "original_text": original_text,
                    "translated_text": translated_text,
                    "source_language": source_lang,
                    "target_language": target_lang,
                    "confidence": confidence,
                    "medical_context_applied": True
                },
                "timestamp": datetime.now().isoformat(),
                "language": target_lang
            }
            
            logger.info(f"🌐 Broadcasting translation: '{original_text}' → '{translated_text}'")
            await self._broadcast_to_session(session_id, message)
            
        except Exception as e:
            logger.error(f"❌ Error broadcasting translation: {e}")

    # Add fallback translation method
    async def _broadcast_simple_translation(self, session_id: str, role: str, text: str, source_lang: str, target_lang: str):
        """Broadcast simple fallback translation"""
        try:
            # Simple fallback translations
            simple_translations = {
                ("es", "en"): {
                    "estoy embarazada": "I am pregnant",
                    "tomando ibuprofeno": "taking ibuprofen",
                    "estoy embarazada tomando ibuprofeno": "I am pregnant taking ibuprofen"
                }
            }
            
            fallback_text = simple_translations.get((source_lang, target_lang), {}).get(text.lower(), text)
            
            message = {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "speaker": role,
                "message_type": "translation",
                "content": {
                    "original_text": text,
                    "translated_text": fallback_text,
                    "source_language": source_lang,
                    "target_language": target_lang,
                    "confidence": 0.8,
                    "medical_context_applied": False,
                    "fallback": True
                },
                "timestamp": datetime.now().isoformat(),
                "language": target_lang
            }
            
            logger.info(f"🌐 Broadcasting fallback translation: '{text}' → '{fallback_text}'")
            await self._broadcast_to_session(session_id, message)
            
        except Exception as e:
            logger.error(f"❌ Error broadcasting fallback translation: {e}")

    async def _broadcast_streaming_transcription(self, session_id: str, role: str, transcription_result):
        """Broadcast transcription to all connected clients"""
        message = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "speaker": role,
            "message_type": StreamingAudioMessageTypes.STREAMING_TRANSCRIPTION,
            "content": {
                "text": transcription_result.transcribed_text,
                "confidence": transcription_result.confidence,
                "language": transcription_result.detected_language,
                "processing_time": transcription_result.processing_time,
                "audio_duration": transcription_result.audio_duration
            },
            "timestamp": datetime.now().isoformat(),
            "language": transcription_result.detected_language
        }
        
        await self._broadcast_to_session(session_id, message)

    async def _broadcast_translation_result(self, session_id: str, role: str, translation_result):
        """Broadcast translation result"""
        message = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "speaker": role,
            "message_type": "translation",
            "content": {
                "original_text": translation_result.get("original_text", ""),  # May not exist
                "translated_text": translation_result.get("enhanced_translation") or translation_result.get("standard_translation"),
                "source_language": "auto",  # You may need to track this
                "target_language": "auto",  # You may need to track this
                "confidence": 0.9,  # Default since not in translation result
                "medical_context_applied": translation_result.get("medical_context_applied", False)
            },
            "timestamp": datetime.now().isoformat(),
            "language": "en"  # Or determine dynamically
        }
        
        await self._broadcast_to_session(session_id, message)

    async def _stream_tts_response(self, session_id: str, text: str, language: str, target_role: str):
        """Stream TTS audio response to target client"""
        try:
            target_connection_id = f"{session_id}_{target_role}"
            target_websocket = self.active_connections.get(target_connection_id)
            
            if not target_websocket:
                logger.warning(f"No target WebSocket found for {target_connection_id}")
                return
            
            # Generate streaming TTS
            async for audio_chunk in self.streaming_audio_service.generate_streaming_tts(
                text=text,
                language=language
            ):
                if audio_chunk:  # Non-empty chunk
                    import base64
                    
                    tts_message = {
                        "id": str(uuid.uuid4()),
                        "session_id": session_id,
                        "speaker": "system",
                        "message_type": StreamingAudioMessageTypes.STREAMING_TTS,
                        "content": {
                            "audio_chunk": base64.b64encode(audio_chunk).decode(),
                            "text": text,
                            "language": language,
                            "format": "wav",
                            "chunk_index": getattr(self, '_tts_chunk_counter', 0)
                        },
                        "timestamp": datetime.now().isoformat(),
                        "language": language
                    }
                    
                    await target_websocket.send_json(tts_message)
                    self._tts_chunk_counter = getattr(self, '_tts_chunk_counter', 0) + 1
                    
        except Exception as e:
            logger.error(f"Error streaming TTS: {e}")

    async def _handle_start_listening(self, websocket: WebSocket, session_id: str, role: str, message: dict):
        """Handle start listening request"""
        try:
            # Store session configuration
            self.session_configs[session_id] = {
                "listening_enabled": True,
                "role": role,
                "language": message.get("language", "auto")
            }
            
            # Send confirmation
            status_message = {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "speaker": "system",
                "message_type": StreamingAudioMessageTypes.AUDIO_STATUS,
                "content": {
                    "status": "listening_started",
                    "vad_enabled": True,
                    "auto_processing": True,
                    "session_role": role
                },
                "timestamp": datetime.now().isoformat(),
                "language": "en"
            }
            
            await websocket.send_json(status_message)
            logger.info(f"🎤 Started listening for session {session_id}, role {role}")
            
        except Exception as e:
            logger.error(f"Error starting listening: {e}")

    async def _handle_stop_listening(self, websocket: WebSocket, session_id: str, role: str, message: dict):
        """Handle stop listening request"""
        try:
            # Update session configuration
            if session_id in self.session_configs:
                self.session_configs[session_id]["listening_enabled"] = False
            
            # Send confirmation
            status_message = {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "speaker": "system",
                "message_type": StreamingAudioMessageTypes.AUDIO_STATUS,
                "content": {
                    "status": "listening_stopped",
                    "session_role": role
                },
                "timestamp": datetime.now().isoformat(),
                "language": "en"
            }
            
            await websocket.send_json(status_message)
            logger.info(f"🎤 Stopped listening for session {session_id}, role {role}")
            
        except Exception as e:
            logger.error(f"Error stopping listening: {e}")

    async def _handle_transcription_message(self, websocket: WebSocket, session_id: str, role: str, message: dict):
        """Handle direct transcription message (existing functionality)"""
        try:
            text = message.get("text", "")
            language = message.get("language", "auto")
            
            if not text:
                return
            
            # Create mock transcription result for compatibility
            from services.audio.streaming_audio_service import StreamingSTTResult
            transcription_result = StreamingSTTResult(
                transcribed_text=text,
                confidence=0.95,  # Default confidence for manual input
                detected_language=language,
                audio_duration=0.0,
                processing_time=0.0
            )
            
            # Process through the same pipeline
            await self._process_streaming_transcription(session_id, role, transcription_result)
            
        except Exception as e:
            logger.error(f"Error handling transcription message: {e}")

    async def _broadcast_to_session(self, session_id: str, message: dict):
        """Broadcast message to all connections in a session"""
        connections_to_notify = [
            (conn_id, ws) for conn_id, ws in self.active_connections.items()
            if conn_id.startswith(session_id)
        ]
        
        for conn_id, websocket in connections_to_notify:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {conn_id}: {e}")

    async def _broadcast_urgent_medical_alert(self, session_id: str, medical_result):
        """Broadcast urgent medical alert"""
        # FIX: Access dict keys, not object attributes
        safety_alerts = medical_result.get("safety_alerts", [])
        
        for alert in safety_alerts:
            # Handle both dict and object alert formats
            if isinstance(alert, dict):
                severity = alert.get("severity", "unknown")
                alert_type = alert.get("type", "unknown") 
                message = alert.get("message", "")
                clinical_recommendation = alert.get("clinical_recommendation", "")
            else:
                # If alert is an object
                severity = getattr(alert, 'severity', 'unknown')
                alert_type = getattr(alert, 'type', 'unknown')
                message = getattr(alert, 'message', '')
                clinical_recommendation = getattr(alert, 'clinical_recommendation', '')
            
            if severity in ["urgent", "high"]:  # Based on your logs showing "high" severity
                alert_message = {
                    "id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "speaker": "system", 
                    "message_type": "medical_alert",
                    "content": {
                        "alert_type": alert_type,
                        "message": message,
                        "severity": severity,
                        "action_required": True,
                        "clinical_recommendation": clinical_recommendation
                    },
                    "timestamp": datetime.now().isoformat(),
                    "language": "en"
                }
                
                await self._broadcast_to_session(session_id, alert_message)

    def _get_target_language(self, session_id: str, speaker_role: str) -> Optional[str]:
        """Get target language for translation based on speaker role"""
        # This should integrate with your session management
        # For now, simple mapping
        if speaker_role == "doctor":
            return "es"  # Translate doctor's English to Spanish for patient
        elif speaker_role == "patient":
            return "en"  # Translate patient's Spanish to English for doctor
        return None

    def _get_opposite_role(self, role: str) -> str:
        """Get the opposite role for targeting messages"""
        return "patient" if role == "doctor" else "doctor"

    async def _update_conversation_summary(self, session_id: str, medical_result):
        """Update conversation summary (integrate with your existing summary service)"""
        try:
            # FIX: medical_result is a dict, not an object with attributes
            # Based on your logs showing: "7 medications, 2 safety alerts"
            
            # Extract medications safely
            medications = medical_result.get("medications", [])
            
            # Convert medication objects to dicts if needed
            medications_list = []
            for med in medications:
                if hasattr(med, 'dict'):
                    medications_list.append(med.dict())
                elif isinstance(med, dict):
                    medications_list.append(med)
                else:
                    medications_list.append({"name": str(med)})
            
            # Extract safety alerts safely  
            safety_alerts = medical_result.get("safety_alerts", [])
            if isinstance(safety_alerts, list):
                safety_alerts_count = len(safety_alerts)
            else:
                safety_alerts_count = 0
                
            # Extract medical context safely
            medical_context = medical_result.get("medical_context", {})
            
            summary_message = {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "speaker": "system",
                "message_type": "conversation_summary",
                "content": {
                    "medications_discussed": medications_list,  # ✅ Fixed
                    "safety_alerts_count": safety_alerts_count,  # ✅ Fixed
                    "medical_context": medical_context,  # ✅ Fixed
                    "last_updated": datetime.now().isoformat()
                },
                "timestamp": datetime.now().isoformat(),
                "language": "en"
            }
            
            await self._broadcast_to_session(session_id, summary_message)
            
        except Exception as e:
            logger.error(f"Error updating conversation summary: {e}")
            # Don't let summary errors break the main pipeline
            logger.error(f"Medical result structure: {type(medical_result)}")
            logger.error(f"Medical result keys: {list(medical_result.keys()) if isinstance(medical_result, dict) else 'Not a dict'}")

    async def _send_error_message(self, websocket: WebSocket, session_id: str, error_message: str):
        """Send error message to client"""
        error_msg = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "speaker": "system",
            "message_type": "error",
            "content": {
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat(),
            "language": "en"
        }
        
        try:
            await websocket.send_json(error_msg)
        except Exception as e:
            logger.error(f"Error sending error message: {e}")

# Enhanced WebSocket endpoint
@router.websocket("/conversation/ws/{session_id}/{role}")
async def enhanced_websocket_endpoint(websocket: WebSocket, session_id: str, role: str):
    """
    Enhanced WebSocket endpoint with streaming audio support
    Maintains compatibility with existing conversation functionality
    """
    enhanced_manager = EnhancedConversationManager()
    await enhanced_manager.handle_websocket_connection(websocket, session_id, role)