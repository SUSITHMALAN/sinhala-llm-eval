"""Model clients behind one interface."""

from lankallm.models.base import ModelClient, ModelError, ModelResponse
from lankallm.models.mock import MockClient
from lankallm.models.openai_compatible import OpenAICompatibleClient
from lankallm.models.registry import build_client

__all__ = [
    "MockClient",
    "ModelClient",
    "ModelError",
    "ModelResponse",
    "OpenAICompatibleClient",
    "build_client",
]
