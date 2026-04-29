import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Priority: GROQ_API_KEY → OPENAI_API_KEY
groq_key = os.getenv("GROQ_API_KEY")
groq_base = os.getenv("GROQ_API_BASE")
openai_key = os.getenv("OPENAI_API_KEY")

if groq_key and groq_base:
    client = OpenAI(api_key=groq_key, base_url=groq_base)
    DEFAULT_MODEL = "llama-3.1-8b-instant"
elif openai_key:
    client = OpenAI(api_key=openai_key)
    DEFAULT_MODEL = "gpt-4o-mini"
else:
    raise RuntimeError("No API key found in .env")

def call_llm(prompt: str, model: str = None, temperature: float = 0.2) -> str:
    """Call LLM with retry-friendly defaults."""
    response = client.chat.completions.create(
        model=model or DEFAULT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content
