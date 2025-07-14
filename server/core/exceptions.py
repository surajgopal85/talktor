# core/exceptions.py

"""
Custom exceptions for Talktor application
Provides specific error types for better error handling and user experience
"""

class TalktorException(Exception):
    """Base exception for Talktor application"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class DatabaseError(TalktorException):
    """Database operation errors"""
    pass

class ExternalAPIError(TalktorException):
    """External API communication errors"""
    def __init__(self, message: str, api_name: str = None, status_code: int = None):
        self.api_name = api_name
        self.status_code = status_code
        super().__init__(message, "EXTERNAL_API_ERROR")

class ExtractionError(TalktorException):
    """Medication extraction errors"""
    pass

class TranslationError(TalktorException):
    """Translation service errors"""
    pass

class ValidationError(TalktorException):
    """Input validation errors"""
    pass

class AudioProcessingError(TalktorException):
    """Audio file processing errors"""
    def __init__(self, message: str, file_format: str = None):
        self.file_format = file_format
        super().__init__(message, "AUDIO_PROCESSING_ERROR")

class LearningError(TalktorException):
    """Machine learning and feedback errors"""
    pass

class ConfigurationError(TalktorException):
    """Configuration and setup errors"""
    pass