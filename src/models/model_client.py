"""
Model client abstraction for provider-agnostic LLM interactions.

Based on learnings from CodeFlow - keeps agents independent of specific LLM providers.
"""

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    import google.generativeai as genai  # type: ignore
except ImportError:  # pragma: no cover - handled in runtime guard
    genai = None


@dataclass
class ModelResponse:
    """Standardized response from any model provider."""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None


class ModelClient(ABC):
    """
    Abstract base class for LLM model clients.

    Implementations should handle provider-specific details while
    exposing a consistent interface.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Generate a response from the model.

        Args:
            prompt: The user prompt/message
            system_prompt: Optional system prompt to guide behavior
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Returns:
            ModelResponse with generated content
        """
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate structured output matching a schema.

        Args:
            prompt: The user prompt/message
            schema: JSON schema for the expected output
            system_prompt: Optional system prompt
            **kwargs: Provider-specific parameters

        Returns:
            Parsed structured output matching the schema
        """
        pass


class GoogleModelClient(ModelClient):
    """
    Google Cloud (Gemini) implementation of ModelClient.

    Uses google-generativeai SDK for text and schema-constrained generation.
    """

    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        project_id: Optional[str] = None,
        location: str = "us-central1",
        default_temperature: float = 0.7,
        default_max_tokens: int = 2048,
        api_key: Optional[str] = None
    ):
        """
        Initialize Google model client.

        Args:
            model_name: Name of the Gemini model to use
            project_id: GCP project ID (from env if not provided)
            location: GCP region
            default_temperature: Default sampling temperature
            default_max_tokens: Default max tokens
            api_key: Google Generative AI API key (falls back to GOOGLE_API_KEY env)
        """
        self.model_name = model_name
        self.project_id = project_id
        self.location = location
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")

        self._configured = False
        self._client = None

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Generate response using Google Gemini.
        """
        self._ensure_client()
        temperature = temperature if temperature is not None else self.default_temperature
        max_tokens = max_tokens if max_tokens is not None else self.default_max_tokens

        # Build the full prompt with system context if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        model = self._client or genai.GenerativeModel(self.model_name)
        response = model.generate_content(
            full_prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens
            },
            **kwargs
        )

        content = self._extract_text(response)
        usage = getattr(response, "usage_metadata", None)
        usage_dict = None
        if usage:
            usage_dict = {
                "input_tokens": getattr(usage, "prompt_token_count", None),
                "output_tokens": getattr(usage, "candidates_token_count", None)
            }

        return ModelResponse(
            content=content,
            model=self.model_name,
            usage=usage_dict,
            metadata={"finish_reason": getattr(response, "finish_reason", None)},
            finish_reason=getattr(response, "finish_reason", None)
        )

    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate structured output using Google Gemini.
        """
        self._ensure_client()

        # Build the full prompt with system context if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        model = self._client or genai.GenerativeModel(self.model_name)
        response = model.generate_content(
            full_prompt,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": schema
            },
            **kwargs
        )

        raw_text = self._extract_text(response)
        try:
            return json.loads(raw_text)
        except (json.JSONDecodeError, TypeError):
            return {"raw": raw_text}

    def _ensure_client(self) -> None:
        if genai is None:
            raise ImportError("google-generativeai is not installed. Install per requirements.txt")
        if not self._configured:
            if not self.api_key:
                raise EnvironmentError("GOOGLE_API_KEY not set for Gemini client")
            genai.configure(api_key=self.api_key)
            self._configured = True
        if self._client is None:
            self._client = genai.GenerativeModel(self.model_name)

    @staticmethod
    def _build_messages(prompt: str, system_prompt: Optional[str]) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

    @staticmethod
    def _extract_text(response: Any) -> str:
        if hasattr(response, "text"):
            return response.text
        if hasattr(response, "candidates"):
            candidates = getattr(response, "candidates")
            if candidates:
                content = getattr(candidates[0], "content", None)
                if content and getattr(content, "parts", None):
                    part = content.parts[0]
                    return getattr(part, "text", "") or getattr(part, "data", "")
        return str(response)


def create_model_client(config: Dict[str, Any]) -> ModelClient:
    """
    Factory function to create appropriate model client from config.

    Args:
        config: Configuration dictionary with model settings

    Returns:
        Configured ModelClient instance

    Example config:
        {
            "provider": "google",
            "model_name": "gemini-1.5-pro",
            "temperature": 0.7,
            "max_tokens": 2048
        }
    """
    provider = config.get("provider", "google").lower()

    if provider == "google":
        return GoogleModelClient(
            model_name=config.get("model_name", "gemini-1.5-pro"),
            project_id=config.get("project_id"),
            default_temperature=config.get("temperature", 0.7),
            default_max_tokens=config.get("max_tokens", 2048)
        )
    else:
        raise ValueError(f"Unsupported model provider: {provider}")
