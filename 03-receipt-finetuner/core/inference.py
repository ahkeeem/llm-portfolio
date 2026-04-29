"""
Inference module for receipt field extraction.

Loads the fine-tuned LoRA adapter and runs predictions.
Falls back to OpenAI API if no local model is available.
"""

import json
import os


def extract_receipt_fields(receipt_text: str) -> dict:
    """
    Extract structured fields from receipt text.

    Tries local fine-tuned model first, falls back to OpenAI API.

    Args:
        receipt_text: Raw receipt text.

    Returns:
        Dict with company, date, address, total fields.
    """
    adapter_path = "models/receipt-lora-adapter"

    if os.path.exists(adapter_path):
        return _extract_local(receipt_text, adapter_path)
    else:
        return _extract_api(receipt_text)


def _extract_local(receipt_text: str, adapter_path: str) -> dict:
    """Extract using the locally fine-tuned LoRA model."""
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
        import torch

        tokenizer = AutoTokenizer.from_pretrained(adapter_path)
        base_model = AutoModelForCausalLM.from_pretrained(
            "microsoft/Phi-3-mini-4k-instruct",
            device_map="auto",
            torch_dtype=torch.float16,
        )
        model = PeftModel.from_pretrained(base_model, adapter_path)

        prompt = f"### Receipt:\n{receipt_text}\n\n### Extracted Fields:\n"
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(**inputs, max_new_tokens=200, temperature=0.1)
        result = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Parse the generated JSON
        json_start = result.find("{")
        json_end = result.rfind("}") + 1
        if json_start != -1 and json_end > json_start:
            fields = json.loads(result[json_start:json_end])
        else:
            fields = {"raw_output": result}

        return {"fields": fields, "model": "fine-tuned-local", "requires_review": False}

    except Exception as e:
        return {"error": str(e), "fallback": "api"}


def _extract_api(receipt_text: str) -> dict:
    """Fallback: Extract using LLM API (before fine-tuning is complete)."""
    from openai import OpenAI
    from dotenv import load_dotenv

    load_dotenv()
    groq_key = os.getenv("GROQ_API_KEY")
    groq_base = os.getenv("GROQ_API_BASE")
    openai_key = os.getenv("OPENAI_API_KEY")

    if groq_key and groq_base:
        client = OpenAI(api_key=groq_key, base_url=groq_base)
        model_name = "llama-3.1-8b-instant"
    elif openai_key:
        client = OpenAI(api_key=openai_key)
        model_name = "gpt-4o-mini"
    else:
        return {"error": "No API key found", "requires_review": True}

    prompt = f"""Extract the following fields from this receipt text.
Return JSON only:
{{
  "company": "",
  "date": "",
  "address": "",
  "total": ""
}}

Receipt:
{receipt_text}"""

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        content = response.choices[0].message.content
        fields = json.loads(content)
    except Exception as e:
        fields = {"error": str(e), "raw_output": getattr(response.choices[0].message, "content", "") if 'response' in locals() else ""}

    return {"fields": fields, "model": f"{model_name}-fallback", "requires_review": True}
