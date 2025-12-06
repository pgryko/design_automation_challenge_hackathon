"""
Core services for the Design Automation app.
"""

from .document import extract_content, get_supported_extensions, is_supported
from .gemini import GeminiService
from .style import StyleService

__all__ = [
    "GeminiService",
    "StyleService",
    "extract_content",
    "get_supported_extensions",
    "is_supported",
]
