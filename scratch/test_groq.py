import os
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class ClassificationResponse(BaseModel):
    priority: str
    type: str

groq_key = os.getenv("GROQ_API_KEY")
groq_base = os.getenv("GROQ_API_BASE")

client = OpenAI(api_key=groq_key, base_url=groq_base)
model = "llama-3.1-8b-instant"

def test_structured():
    prompt = "Classify this email: 'I need a refund for my order #123'. Priority: urgent, normal, low. Type: complaint, request, info."
    system_prompt = f"You are a helpful assistant. You must respond in pure JSON. Adhere strictly to this schema: {ClassificationResponse.schema_json()}"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        print(f"Content: {content}")
        data = ClassificationResponse.parse_raw(content)
        print(f"Parsed: {data}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_structured()
