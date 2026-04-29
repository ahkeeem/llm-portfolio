import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Support both Groq (free) and OpenAI
# Priority: GROQ_API_KEY → OPENAI_API_KEY
groq_key = os.getenv("GROQ_API_KEY")
groq_base = os.getenv("GROQ_API_BASE")
openai_key = os.getenv("OPENAI_API_KEY")

if groq_key and groq_base:
    # Using Groq (free tier)
    client = OpenAI(api_key=groq_key, base_url=groq_base)
    DEFAULT_MODEL = "llama-3.1-8b-instant"
    PROVIDER = "groq"
elif openai_key:
    # Using OpenAI
    client = OpenAI(api_key=openai_key)
    DEFAULT_MODEL = "gpt-4o-mini"
    PROVIDER = "openai"
else:
    raise RuntimeError(
        "No API key found. Set GROQ_API_KEY + GROQ_API_BASE or OPENAI_API_KEY in .env"
    )

print(f"✅ LLM Provider: {PROVIDER} | Model: {DEFAULT_MODEL}")


def call_llm(prompt: str, model: str = None, temperature: float = 0.3) -> str:
    """
    Call LLM (Groq or OpenAI) with retry-friendly defaults.

    Args:
        prompt: The user prompt to send.
        model: Model override. Defaults to provider-appropriate model.
        temperature: Sampling temperature (lower = more deterministic).

    Returns:
        The assistant's response content as a string.
    """
    response = client.chat.completions.create(
        model=model or DEFAULT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content
