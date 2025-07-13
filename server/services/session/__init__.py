# =============================================================================
# services/session/__init__.py
# =============================================================================

"""
Session Management Services

Handles session lifecycle, storage, and analytics:
- Session creation and management
- Data storage and retrieval
- Analytics and reporting
"""

from .manager import SessionService

__all__ = ["SessionService"]