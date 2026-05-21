"""
Unified LLM Service — single entry point for all model calls.

Replaces the duplicated OpenAI/Groq client initialisations scattered
across projects 01–04 and the control plane.  All model calls should
flow through this module.

Features (as per ARCHITECTURE.md §12):
    • Provider auto-detection (Groq → OpenAI fallback)
    • Exponential-backoff retries (max 3)
    • Token accounting via MetricsCollector
    • Structured JSON output enforcement
    • Template-driven prompts via the prompt registry
    • Timeout handling
"""
import json
import logging
import os
import re
from typing import Type, TypeVar, Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from tenacity import retry, wait_exponential, stop_after_attempt

from core.observability.metrics import metrics

load_dotenv()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Provider auto-detection
# ---------------------------------------------------------------------------
_groq_key = os.getenv("GROQ_API_KEY")
_groq_base = os.getenv("GROQ_API_BASE")
_openai_key = os.getenv("OPENAI_API_KEY")

if _groq_key and _groq_base:
    _client = OpenAI(api_key=_groq_key, base_url=_groq_base)
    _DEFAULT_MODEL = "llama-3.1-8b-instant"
    _PROVIDER = "groq"
elif _openai_key:
    _client = OpenAI(api_key=_openai_key)
    _DEFAULT_MODEL = "gpt-4o-mini"
    _PROVIDER = "openai"
else:
    _client = None
    _DEFAULT_MODEL = "none"
    _PROVIDER = "none"
    logger.warning("No LLM API key found. LLMService calls will fail at runtime.")

logger.info("LLMService initialised — provider=%s model=%s", _PROVIDER, _DEFAULT_MODEL)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
T = TypeVar("T", bound=BaseModel)


class LLMService:
    """Unified facade for all LLM interactions."""

    provider = _PROVIDER
    default_model = _DEFAULT_MODEL

    # ---- Free-text generation -----------------------------------------

    @staticmethod
    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
    def generate(
        prompt: str,
        model: str = None,
        temperature: float = 0.3,
        project: str = "unknown",
    ) -> str:
        """
        Generate a free-text completion.

        Args:
            prompt: The user prompt string.
            model: Override the default model.
            temperature: Sampling temperature.
            project: Project label for token accounting.

        Returns:
            The LLM's text response.
        """
        response = _client.chat.completions.create(
            model=model or _DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        _track_usage(response, model, project)
        return response.choices[0].message.content

    # ---- Structured (JSON) generation ---------------------------------

    @staticmethod
    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
    def generate_structured(
        prompt: str,
        response_model: Type[T],
        model: str = None,
        project: str = "unknown",
    ) -> T:
        """
        Generate a response and validate it against a Pydantic schema.

        Args:
            prompt: The user prompt string.
            response_model: Pydantic model class for validation.
            model: Override the default model.
            project: Project label for token accounting.

        Returns:
            A validated Pydantic model instance.
        """
        system_prompt = (
            "You are a helpful assistant. You must respond in pure JSON. "
            f"Adhere strictly to this schema: {response_model.model_json_schema()}"
        )
        response = _client.chat.completions.create(
            model=model or _DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        _track_usage(response, model, project)

        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM returned empty content")

        # Strip markdown fences
        content = content.strip()
        if content.startswith("```"):
            content = re.sub(r"```(?:json)?\n?|```", "", content).strip()

        try:
            data = json.loads(content)
            # Auto-unwrap single top-level key if it's not in the schema
            if len(data) == 1 and isinstance(list(data.values())[0], dict):
                first_key = list(data.keys())[0]
                if first_key.lower() not in response_model.model_fields:
                    data = data[first_key]
            return response_model.model_validate(data)
        except Exception as e:
            logger.error("Structured parse failed: %s\nContent: %s", e, content)
            raise

    # ---- Template-driven generation -----------------------------------

    @staticmethod
    def generate_from_template(
        template_name: str,
        model: str = None,
        temperature: float = 0.3,
        project: str = "unknown",
        **template_vars,
    ) -> str:
        """
        Render a Jinja2 prompt template and generate a completion.

        Args:
            template_name: Name of the template (without .j2 extension).
            **template_vars: Variables to substitute into the template.

        Returns:
            The LLM's text response.
        """
        from core.prompts import render_prompt

        prompt = render_prompt(template_name, **template_vars)
        return LLMService.generate(
            prompt, model=model, temperature=temperature, project=project
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _track_usage(response, model: Optional[str], project: str):
    """Record token usage from an API response."""
    usage = getattr(response, "usage", None)
    if usage:
        metrics.record_tokens(
            prompt_tokens=usage.prompt_tokens or 0,
            completion_tokens=usage.completion_tokens or 0,
            model=model or _DEFAULT_MODEL,
            project=project,
        )
