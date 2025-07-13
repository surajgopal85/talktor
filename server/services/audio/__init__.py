# =============================================================================
# services/audio/__init__.py
# =============================================================================

"""
Audio Processing Services

Speech-to-text and text-to-speech services:
- Whisper integration for STT
- TTS processing (future)
"""

from .whisper_service import WhisperService

__all__ = ["WhisperService"]