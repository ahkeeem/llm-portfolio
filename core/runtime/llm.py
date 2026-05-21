import os
from openai import OpenAI
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt
from core.observability.metrics import metrics
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Support both Groq (free) and OpenAI
# Priority: GROQ_API_KEY → OPENAI_API_KEY
groq_key = os.getenv("GROQ_API_KEY")
groq_base = os.getenv("GROQ_API_BASE")
openai_key = os.getenv("OPENAI_API_KEY")

if groq_key and groq_base:
    client = OpenAI(api_key=groq_key, base_url=groq_base)
    DEFAULT_MODEL = "llama-3.1-8b-instant"
    PROVIDER = "groq"
elif openai_key:
    client = OpenAI(api_key=openai_key)
    DEFAULT_MODEL = "gpt-4o-mini"
    PROVIDER = "openai"
else:
    raise RuntimeError(
        "No API key found. Set GROQ_API_KEY + GROQ_API_BASE or OPENAI_API_KEY in .env"
    )

print(f"✅ LLM Provider: {PROVIDER} | Model: {DEFAULT_MODEL}")


import json
import re
from pydantic import BaseModel
from typing import TypeVar, Type, Optional

T = TypeVar('T', bound=BaseModel)

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
def call_llm_structured(prompt: str, response_model: Type[T], model: str = None, project: str = "unknown") -> T:
    """
    Call LLM and enforce structured JSON output matching the provided Pydantic model.
    Hardened to handle markdown blocks and potential LLM wrapping.
    """
    system_prompt = f"You are a helpful assistant. You must respond in pure JSON. Adhere strictly to this schema: {response_model.model_json_schema()}"
    
    response = client.chat.completions.create(
        model=model or DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    
    usage = getattr(response, "usage", None)
    if usage:
        metrics.record_tokens(
            prompt_tokens=usage.prompt_tokens or 0,
            completion_tokens=usage.completion_tokens or 0,
            model=model or DEFAULT_MODEL,
            project=project
        )
        
    content = response.choices[0].message.content
    if not content:
        raise ValueError("LLM returned empty content")

    # Clean potential markdown wrapping
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"```(?:json)?\n?|```", "", content).strip()
    
    try:
        data = json.loads(content)
        # Some LLMs wrap the JSON in a top-level key like 'classification' or 'data'
        if len(data) == 1 and isinstance(list(data.values())[0], dict):
             # If the schema doesn't have this top-level key but the data does, unwrap it
             first_key = list(data.keys())[0]
             if first_key.lower() not in response_model.model_fields:
                 data = data[first_key]
                 
        return response_model.model_validate(data)
    except Exception as e:
        logger.error(f"Failed to parse LLM structured output: {e}\nContent: {content}")
        raise

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
def call_llm(prompt: str, model: str = None, temperature: float = 0.3, project: str = "unknown") -> str:
    """Call LLM with retry-friendly defaults and token tracking."""
    response = client.chat.completions.create(
        model=model or DEFAULT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )

    # Track real token usage from the API response
    usage = getattr(response, "usage", None)
    if usage:
        metrics.record_tokens(
            prompt_tokens=usage.prompt_tokens or 0,
            completion_tokens=usage.completion_tokens or 0,
            model=model or DEFAULT_MODEL,
            project=project
        )

    return response.choices[0].message.content
