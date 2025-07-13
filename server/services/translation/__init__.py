# =============================================================================
# services/translation/__init__.py
# =============================================================================

"""
Translation Services

Handles translation with medical context awareness:
- General translation logic
- Medical-specific translation enhancements
- Follow-up question generation
"""

from .translator import TranslationService

__all__ = ["TranslationService"]