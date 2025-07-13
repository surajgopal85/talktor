# =============================================================================
# services/audio/whisper_service.py
# =============================================================================

import logging
import tempfile
import os
import whisper
from typing import Dict

logger = logging.getLogger(__name__)

class WhisperService:
    """Whisper speech-to-text service"""
    
    def __init__(self, model_name: str = "base"):
        self.model = whisper.load_model(model_name)
        logger.info(f"🎤 Whisper model '{model_name}' loaded")
    
    async def transcribe_audio(self, audio_content: bytes, file_extension: str = ".wav") -> Dict:
        """Transcribe audio content to text"""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp:
            tmp.write(audio_content)
            tmp_path = tmp.name
        
        try:
            # Transcribe using Whisper
            logger.info("🎤 Transcribing audio...")
            result = self.model.transcribe(tmp_path)
            
            return {
                "text": result["text"],
                "language": result.get("language"),
                "confidence": result.get("confidence"),
                "segments": result.get("segments", [])
            }
            
        finally:
            # Clean up temporary file
            os.remove(tmp_path)