"""Abstract LLM provider interface.

ALL LLM calls in this application MUST go through a LLMProvider implementation.
This ensures testability, vendor swappability, and a single place to add
observability (tokens, latency, cost).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Vendor-agnostic LLM provider.

    Implementations must return a validated Pydantic model, forcing
    structured JSON output via whatever mechanism the backend supports
    (tool-use, JSON mode, constrained decoding, etc.).
    """

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        schema: type[T],
        *,
        system: str | None = None,
    ) -> T:
        """
        Send prompt to the LLM and return a validated instance of `schema`.

        Args:
            prompt:  User-turn message.
            schema:  Pydantic model class; the provider must ensure the
                     response conforms to this schema.
            system:  Optional system-turn text.

        Returns:
            A validated instance of `schema`.

        Raises:
            LLMProviderError: on any unrecoverable API or parse failure.
        """
        ...


class LLMProviderError(Exception):
    """Raised when the LLM provider cannot fulfil the request."""
