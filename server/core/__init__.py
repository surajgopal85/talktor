# core/__init__.py

"""
Core Configuration and Utilities Package

Provides application-wide configuration, logging, and exception handling:
- Environment-based configuration management
- Structured logging with file rotation
- Custom exceptions for better error handling
- Security and validation utilities
"""

from .config import settings, Settings
from .exceptions import (
    TalktorException,
    DatabaseError,
    ExternalAPIError,
    ExtractionError,
    TranslationError,
    ValidationError,
    AudioProcessingError,
    LearningError,
    ConfigurationError
)

__all__ = [
    "settings",
    "Settings",
    "TalktorException",
    "DatabaseError", 
    "ExternalAPIError",
    "ExtractionError",
    "TranslationError",
    "ValidationError",
    "AudioProcessingError",
    "LearningError",
    "ConfigurationError"
]