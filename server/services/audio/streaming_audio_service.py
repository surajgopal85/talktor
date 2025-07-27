# services/audio/streaming_audio_service.py
import asyncio
import time
import logging
import io
import base64
from typing import Optional, Dict, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import uuid

import numpy as np
from pydub import AudioSegment
import speech_recognition as sr
import openai

logger = logging.getLogger(__name__)

@dataclass
class StreamingSTTResult:
    """Result of streaming speech-to-text processing"""
    transcribed_text: str
    confidence: float
    detected_language: str = "unknown"
    audio_duration: float = 0.0
    processing_time: float = 0.0
    error: Optional[str] = None

@dataclass
class StreamingState:
    """State tracking for streaming audio session"""
    is_recording: bool = False
    is_processing: bool = False
    last_speech_time: Optional[float] = None
    current_speaker: Optional[str] = None
    session_start_time: float = 0.0

class AudioBuffer:
    """
    Circular audio buffer for accumulating speech segments
    """
    
    def __init__(self, max_duration: float = 10.0, sample_rate: int = 16000):
        self.max_duration = max_duration
        self.sample_rate = sample_rate
        self.chunks = []
        self.total_samples = 0
        
    def add_chunk(self, audio_chunk: bytes):
        """Add audio chunk to buffer"""
        # Assume 16-bit audio (2 bytes per sample)
        samples_in_chunk = len(audio_chunk) // 2
        self.chunks.append(audio_chunk)
        self.total_samples += samples_in_chunk
        
        # Remove old chunks if buffer exceeds max duration
        max_samples = int(self.max_duration * self.sample_rate)
        while self.total_samples > max_samples and self.chunks:
            removed_chunk = self.chunks.pop(0)
            self.total_samples -= len(removed_chunk) // 2
    
    def get_duration(self) -> float:
        """Get current buffer duration in seconds"""
        return self.total_samples / self.sample_rate
    
    def to_wav(self) -> bytes:
        """Convert buffer to WAV audio data"""
        if not self.chunks:
            return b""
            
        # Concatenate all chunks
        combined_audio = b"".join(self.chunks)
        
        # Create AudioSegment
        try:
            audio_segment = AudioSegment(
                data=combined_audio,
                sample_width=2,  # 16-bit
                frame_rate=self.sample_rate,
                channels=1
            )
            
            # Export as WAV
            wav_buffer = io.BytesIO()
            audio_segment.export(wav_buffer, format="wav")
            return wav_buffer.getvalue()
        except Exception as e:
            logger.error(f"Error converting audio buffer to WAV: {e}")
            return b""
    
    def clear(self):
        """Clear the buffer"""
        self.chunks.clear()
        self.total_samples = 0

class StreamingAudioService:
    """
    Real-time streaming audio processing service for medical conversations
    Handles continuous STT/TTS with voice activity detection
    """
    
    def __init__(self):
        # Voice Activity Detection settings
        self.vad_threshold = 0.01  # RMS threshold for speech detection
        self.silence_duration = 1.5  # Seconds of silence before processing
        self.min_audio_length = 0.5  # Minimum audio length to process (seconds)
        self.max_audio_length = 30.0  # Maximum audio length (seconds)
        
        # Audio configuration
        self.sample_rate = 16000
        self.audio_format = "wav"
        
        # Session management
        self.audio_buffers: Dict[str, AudioBuffer] = {}
        self.processing_states: Dict[str, StreamingState] = {}
        self.websocket_connections: Dict[str, object] = {}  # session_id -> websocket
        
        # Speech recognition setup
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        
        # OpenAI Whisper setup (assuming you have API key)
        # Alternative: use local Whisper model
        self.use_openai_whisper = True
        
        logger.info("🎤 StreamingAudioService initialized")

    async def start_streaming_session(self, session_id: str, websocket) -> None:
        """
        Initialize streaming audio session for a conversation
        """
        try:
            # Create audio buffer and state
            self.audio_buffers[session_id] = AudioBuffer(
                max_duration=self.max_audio_length,
                sample_rate=self.sample_rate
            )
            
            self.processing_states[session_id] = StreamingState(
                session_start_time=time.time()
            )
            
            self.websocket_connections[session_id] = websocket
            
            logger.info(f"🎤 Started streaming audio session: {session_id}")
            
            # Send initialization confirmation
            await self._send_audio_status(session_id, {
                "status": "streaming_initialized",
                "vad_enabled": True,
                "sample_rate": self.sample_rate,
                "silence_threshold": self.silence_duration
            })
            
        except Exception as e:
            logger.error(f"Failed to start streaming session {session_id}: {e}")
            raise

    async def process_audio_chunk(
        self, 
        session_id: str, 
        audio_chunk_base64: str,
        expected_language: str = "auto"
    ) -> Optional[StreamingSTTResult]:
        """
        Process incoming audio chunk with voice activity detection
        Returns transcription result if speech segment is complete
        """
        try:
            # Get session components
            buffer = self.audio_buffers.get(session_id)
            state = self.processing_states.get(session_id)
            
            if not buffer or not state:
                logger.error(f"No streaming session found for {session_id}")
                return None

            # Decode base64 audio
            try:
                audio_chunk = base64.b64decode(audio_chunk_base64)
            except Exception as e:
                logger.error(f"Failed to decode audio chunk: {e}")
                return None

            # Voice Activity Detection
            audio_level = self._calculate_audio_level(audio_chunk)
            has_speech = audio_level > self.vad_threshold
            
            current_time = time.time()
            
            # Send real-time audio level feedback
            await self._send_audio_status(session_id, {
                "status": "listening",
                "audio_level": round(audio_level, 3),
                "has_speech": has_speech,
                "buffer_duration": round(buffer.get_duration(), 2)
            })
            
            if has_speech:
                # Speech detected - start/continue recording
                state.last_speech_time = current_time
                if not state.is_recording:
                    state.is_recording = True
                    logger.debug(f"🎤 Started recording speech for session {session_id}")
                
                buffer.add_chunk(audio_chunk)
                
            elif state.is_recording and state.last_speech_time:
                # Check if we've had enough silence to process
                silence_duration = current_time - state.last_speech_time
                
                if silence_duration >= self.silence_duration:
                    # Process accumulated audio
                    buffer_duration = buffer.get_duration()
                    
                    if buffer_duration >= self.min_audio_length:
                        logger.info(f"🎤 Processing speech segment: {buffer_duration:.2f}s")
                        
                        result = await self._process_audio_buffer(
                            session_id, buffer, expected_language
                        )
                        
                        # Clear buffer and reset recording state
                        buffer.clear()
                        state.is_recording = False
                        state.last_speech_time = None
                        
                        return result
                    else:
                        # Audio too short, discard
                        logger.debug(f"🎤 Discarding short audio segment: {buffer_duration:.2f}s")
                        buffer.clear()
                        state.is_recording = False
                        state.last_speech_time = None
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing audio chunk for session {session_id}: {e}")
            return StreamingSTTResult(
                transcribed_text="",
                confidence=0.0,
                error=str(e)
            )

    async def _process_audio_buffer(
        self, 
        session_id: str, 
        buffer: AudioBuffer, 
        expected_language: str
    ) -> StreamingSTTResult:
        """
        Process complete audio buffer for transcription
        """
        state = self.processing_states[session_id]
        processing_start_time = time.time()
        
        try:
            state.is_processing = True
            
            # Send processing status
            await self._send_audio_status(session_id, {
                "status": "processing",
                "buffer_duration": buffer.get_duration()
            })
            
            # Convert buffer to WAV
            wav_data = buffer.to_wav()
            if not wav_data:
                raise Exception("Failed to convert audio buffer to WAV")
            
            # Transcribe audio
            if self.use_openai_whisper:
                transcription_result = await self._transcribe_with_openai_whisper(
                    wav_data, expected_language
                )
            else:
                transcription_result = await self._transcribe_with_local_whisper(
                    wav_data, expected_language
                )
            
            processing_time = time.time() - processing_start_time
            
            # Create result
            result = StreamingSTTResult(
                transcribed_text=transcription_result.get("text", "").strip(),
                confidence=transcription_result.get("confidence", 0.0),
                detected_language=transcription_result.get("language", expected_language),
                audio_duration=buffer.get_duration(),
                processing_time=processing_time
            )
            
            logger.info(
                f"🎤 Transcription complete: '{result.transcribed_text}' "
                f"(confidence: {result.confidence:.2f}, time: {processing_time:.2f}s)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Audio processing failed for session {session_id}: {e}")
            return StreamingSTTResult(
                transcribed_text="",
                confidence=0.0,
                error=str(e),
                processing_time=time.time() - processing_start_time
            )
        finally:
            state.is_processing = False

    async def _transcribe_with_openai_whisper(self, wav_data: bytes, language: str) -> dict:
        """
        Transcribe audio using OpenAI Whisper API
        """
        try:
            # Create temporary file-like object
            audio_file = io.BytesIO(wav_data)
            audio_file.name = "audio.wav"
            
            # Call OpenAI Whisper API
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    language=language if language != "auto" else None,
                    response_format="verbose_json"
                )
            )
            
            return {
                "text": response.get("text", ""),
                "language": response.get("language", language),
                "confidence": 0.9  # OpenAI doesn't provide confidence, use default high value
            }
            
        except Exception as e:
            logger.error(f"OpenAI Whisper transcription failed: {e}")
            return {"text": "", "language": language, "confidence": 0.0}

    async def _transcribe_with_local_whisper(self, wav_data: bytes, language: str) -> dict:
        """
        Transcribe audio using local speech recognition (fallback)
        """
        try:
            # Convert WAV data to AudioData
            audio_file = io.BytesIO(wav_data)
            
            with sr.AudioFile(audio_file) as source:
                audio_data = self.recognizer.record(source)
            
            # Use Google Speech Recognition as fallback
            text = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.recognizer.recognize_google(
                    audio_data, 
                    language=language if language != "auto" else None
                )
            )
            
            return {
                "text": text,
                "language": language,
                "confidence": 0.8  # Default confidence for Google STT
            }
            
        except sr.UnknownValueError:
            logger.debug("Speech not recognized")
            return {"text": "", "language": language, "confidence": 0.0}
        except Exception as e:
            logger.error(f"Local speech recognition failed: {e}")
            return {"text": "", "language": language, "confidence": 0.0}

    def _calculate_audio_level(self, audio_chunk: bytes) -> float:
        """
        Calculate RMS audio level for voice activity detection
        """
        try:
            # Convert bytes to numpy array (assuming 16-bit PCM)
            audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
            
            if len(audio_array) == 0:
                return 0.0
            
            # Calculate RMS (Root Mean Square)
            rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
            
            # Normalize to 0-1 range (16-bit audio max value is 32767)
            normalized_rms = min(rms / 32767.0, 1.0)
            
            return float(normalized_rms)  # Convert numpy.float32 to regular float
            
        except Exception as e:
            logger.error(f"Audio level calculation failed: {e}")
            return 0.0

    async def _send_audio_status(self, session_id: str, status_data: dict):
        """
        Send audio status update to WebSocket client
        """
        try:
            websocket = self.websocket_connections.get(session_id)
            if not websocket:
                return
            
            message = {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "speaker": "system",
                "message_type": "audio_status",
                "content": status_data,
                "timestamp": datetime.now().isoformat(),
                "language": "en"
            }
            
            # Send to WebSocket (assuming send_json method exists)
            if hasattr(websocket, 'send_json'):
                await websocket.send_json(message)
            elif hasattr(websocket, 'send'):
                import json
                await websocket.send(json.dumps(message))
                
        except Exception as e:
            logger.error(f"Failed to send audio status: {e}")

    async def generate_streaming_tts(
        self, 
        text: str, 
        language: str = "en",
        voice_config: dict = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Generate streaming TTS audio chunks for real-time playback
        """
        try:
            # For now, generate complete TTS and chunk it
            # Future: implement true streaming TTS
            tts_audio = await self._generate_tts_audio(text, language, voice_config)
            
            if not tts_audio:
                logger.error(f"TTS generation failed for text: {text}")
                return
            
            # Stream audio in chunks for smooth playback
            chunk_size = 4096  # 4KB chunks
            audio_stream = io.BytesIO(tts_audio)
            
            while True:
                chunk = audio_stream.read(chunk_size)
                if not chunk:
                    break
                yield chunk
                
                # Small delay for streaming effect
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"TTS streaming failed: {e}")
            yield b""  # Send empty chunk to indicate error

    async def _generate_tts_audio(self, text: str, language: str, voice_config: dict = None) -> bytes:
        """
        Generate TTS audio using available TTS service
        This should integrate with your existing TTS service
        """
        try:
            # Placeholder for TTS generation
            # Replace with your actual TTS service call
            from gtts import gTTS
            import io
            
            # Use gTTS for demonstration (replace with better TTS)
            tts = gTTS(text=text, lang=language[:2], slow=False)
            
            # Generate audio
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            return audio_buffer.read()
            
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return b""

    async def cleanup_session(self, session_id: str):
        """
        Clean up streaming session resources
        """
        try:
            # Remove session data
            self.audio_buffers.pop(session_id, None)
            self.processing_states.pop(session_id, None)
            self.websocket_connections.pop(session_id, None)
            
            logger.info(f"🎤 Cleaned up streaming session: {session_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {e}")

# Service factory function
def get_streaming_audio_service() -> StreamingAudioService:
    """
    Get singleton instance of StreamingAudioService
    """
    if not hasattr(get_streaming_audio_service, '_instance'):
        get_streaming_audio_service._instance = StreamingAudioService()
    return get_streaming_audio_service._instance