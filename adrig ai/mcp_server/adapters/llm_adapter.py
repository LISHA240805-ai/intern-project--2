import os
import json
import requests

TOOL = {
    "tool_name": "llm_generate",
    "input_schema": {"required": ["prompt"]},
    "description": "Generate or refine text using an LLM (GROQ if configured, otherwise OpenAI or a local fallback)"
}


def _use_groq():
    return os.environ.get("GROQ_API_KEY") is not None


def _use_openai():
    return os.environ.get("OPENAI_API_KEY") is not None


def _groq_request(prompt, model):
    api_key = os.environ.get("GROQ_API_KEY")
    endpoint = os.environ.get("GROQ_API_URL") or f"https://api.groq.com/v1/models/{model}/infer"
    payload = {"input": prompt}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    resp = requests.post(endpoint, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict):
        if "output" in data:
            return data["output"]
        if "result" in data:
            return data["result"]
        if "text" in data:
            return data["text"]
    return json.dumps(data)


def handler(input_data):
    prompt = (input_data or {}).get("prompt", "")
    model = (input_data or {}).get("model", os.environ.get("GROQ_MODEL") or "groq-1")

    if _use_groq():
        try:
            text = _groq_request(prompt, model)
            return {"model": model, "text": text}
        except Exception as e:
            return {"error": "GROQ call failed: %s" % str(e)}

    if _use_openai():
        try:
            import openai
            openai.api_key = os.environ.get("OPENAI_API_KEY")
            try:
                resp = openai.ChatCompletion.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=512,
                )
                text = resp.choices[0].message.content.strip()
                return {"model": model, "text": text, "raw": resp}
            except Exception:
                resp = openai.Completion.create(model=model, prompt=prompt, max_tokens=512)
                text = resp.choices[0].text.strip()
                return {"model": model, "text": text, "raw": resp}
        except Exception as e:
            return {"error": "OpenAI call failed: %s" % str(e)}

    try:
        if "CONTEXT:" in prompt:
            parts = prompt.split("CONTEXT:")
            context = parts[1].strip()
            text = f"Answer based on context: {context[:512]}"
        else:
            text = f"Generated text: {prompt[:512]}"
        return {"model": "local_stub", "text": text}
    except Exception as e:
        return {"error": str(e)}
