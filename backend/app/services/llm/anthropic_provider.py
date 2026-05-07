"""Anthropic Claude implementation of LLMProvider.

Primary path:  tool_use / tool_choice to guarantee structured JSON output.
Fallback path: when the endpoint does not honour tool_choice (e.g. custom
               proxies), we ask for raw JSON inside a markdown fence and
               extract it from the text response.
"""
from __future__ import annotations

import json
import logging
import re
from typing import TypeVar

import anthropic
from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.services.llm.provider import LLMProvider, LLMProviderError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

settings = get_settings()

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_BARE_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(text: str) -> dict:
    """Extract the first JSON object from a text response."""
    m = _JSON_FENCE_RE.search(text)
    if m:
        return json.loads(m.group(1))
    m = _BARE_JSON_RE.search(text)
    if m:
        return json.loads(m.group(0))
    raise ValueError("No JSON object found in LLM response text.")


class AnthropicProvider(LLMProvider):
    """Calls Anthropic Claude and returns a validated Pydantic model.

    Strategy:
    1. Try tool_use with tool_choice=forced — most reliable.
    2. If the response contains no tool_use block (proxy doesn't support it),
       fall back to a plain-text JSON request and parse the response manually.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        base_url: str | None = None,
    ) -> None:
        client_kwargs: dict = {
            "api_key": api_key or settings.anthropic_api_key,
            "timeout": 180.0,   # 3 dakika — büyük promptlar için
            "max_retries": 3,
        }
        if base_url:
            client_kwargs["base_url"] = base_url
        self._client = anthropic.AsyncAnthropic(**client_kwargs)
        self._model = model or settings.llm_model
        self._max_tokens = max_tokens or settings.llm_max_tokens

    async def complete(
        self,
        prompt: str,
        schema: type[T],
        *,
        system: str | None = None,
    ) -> T:
        tool_name = "structured_output"
        tool_def = {
            "name": tool_name,
            "description": (
                f"Return a structured {schema.__name__} object. "
                "Always call this tool with your complete analysis."
            ),
            "input_schema": schema.model_json_schema(),
        }

        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=system or "",
                messages=[{"role": "user", "content": prompt}],
                tools=[tool_def],
                tool_choice={"type": "tool", "name": tool_name},
            )
        except anthropic.APIError as exc:
            raise LLMProviderError(f"Anthropic API error: {exc}") from exc

        tool_block = next(
            (b for b in response.content if b.type == "tool_use"),
            None,
        )

        if tool_block is not None:
            raw_input = tool_block.input
            if isinstance(raw_input, str):
                try:
                    raw_input = json.loads(raw_input)
                except json.JSONDecodeError as exc:
                    raise LLMProviderError(
                        f"tool_use input is not valid JSON: {exc}"
                    ) from exc
        else:
            logger.warning(
                "AnthropicProvider: no tool_use block (stop_reason=%s) — "
                "falling back to JSON text extraction",
                response.stop_reason,
            )
            raw_input = await self._complete_json_fallback(prompt, schema, system)

        try:
            result = schema.model_validate(raw_input)
        except ValidationError as exc:
            raise LLMProviderError(
                f"LLM output failed schema validation ({schema.__name__}): {exc}"
            ) from exc

        logger.info(
            "AnthropicProvider.complete: model=%s schema=%s",
            self._model,
            schema.__name__,
        )
        return result

    async def _complete_json_fallback(
        self,
        prompt: str,
        schema: type[T],
        system: str | None,
    ) -> dict:
        """Re-send the request without tools, asking for raw JSON output."""
        schema_str = json.dumps(schema.model_json_schema(), indent=2)
        json_prompt = (
            f"{prompt}\n\n"
            f"IMPORTANT: Respond with a single valid JSON object that conforms "
            f"exactly to this JSON Schema. Do not include any text outside the JSON object.\n\n"
            f"```json-schema\n{schema_str}\n```\n\n"
            f"Return ONLY the JSON object, wrapped in ```json ... ``` fences."
        )
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=system or "",
                messages=[{"role": "user", "content": json_prompt}],
            )
        except anthropic.APIError as exc:
            raise LLMProviderError(f"Anthropic API error (fallback): {exc}") from exc

        text_blocks = [b for b in response.content if hasattr(b, "text")]
        if not text_blocks:
            raise LLMProviderError("Fallback: LLM returned no text content.")

        full_text = "\n".join(b.text for b in text_blocks)
        try:
            return _extract_json(full_text)
        except (ValueError, json.JSONDecodeError) as exc:
            raise LLMProviderError(
                f"Fallback: could not extract JSON from response: {exc}\n"
                f"Raw text (first 500 chars): {full_text[:500]}"
            ) from exc
