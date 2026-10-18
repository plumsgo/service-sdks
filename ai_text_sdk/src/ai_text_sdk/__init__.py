"""AI Text SDK.

HTTP client for the text generation service. Callers mint the service ticket.
"""

from ai_text_sdk.client import AiTextClient
from ai_text_sdk.errors import AiTextError

__version__ = "1.0.0"

__all__ = [
    "AiTextError",
    "AiTextClient",
]
