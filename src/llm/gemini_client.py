"""Lightweight Gemini client wrapper for hackathon workflow."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from google import genai
from google.genai import types as genai_types


@dataclass
class GeminiConfig:
    api_key: str
    model: str = "gemini-2.0-flash"
    api_url: Optional[str] = None

    @classmethod
    def from_env(cls) -> "GeminiConfig":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is required to initialize Gemini client")
        model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        api_url = os.getenv("GEMINI_API_URL")
        return cls(api_key=api_key, model=model, api_url=api_url)


class GeminiLLM:
    """Thin wrapper around google-genai client with sensible defaults."""

    def __init__(self, config: GeminiConfig | None = None) -> None:
        self.config = config or GeminiConfig.from_env()
        client_options: Dict[str, Any] = {"api_key": self.config.api_key}
        if self.config.api_url:
            client_options["api_endpoint"] = self.config.api_url
        self._client = genai.Client(**client_options)

    @property
    def model(self) -> str:
        return self.config.model

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response for a simple text prompt."""
        request = genai_types.GenerateContentRequest(
            model=self.config.model,
            contents=[genai_types.Content(role="user", parts=[genai_types.Part(text=prompt)])],
            **kwargs,
        )
        response = self._client.responses.generate(request)
        if not response or not response.candidates:
            raise RuntimeError("Gemini returned no candidates for the prompt")
        text_parts = [part.text for part in response.candidates[0].content.parts if getattr(part, "text", None)]
        return "".join(text_parts)

    def generate_structured(
        self,
        contents: list[genai_types.Content],
        **kwargs: Any,
    ) -> genai_types.GenerateContentResponse:
        """Call Gemini with pre-built contents for advanced workflows."""
        request = genai_types.GenerateContentRequest(
            model=self.config.model,
            contents=contents,
            **kwargs,
        )
        return self._client.responses.generate(request)
