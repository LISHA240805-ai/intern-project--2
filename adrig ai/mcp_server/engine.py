import registry
from validator import validate
import requests


def execute(tool_name, input_data):
    tools = registry.get_registry()
    tool = tools.get(tool_name)

    if not tool:
        return {"error": "Tool not found"}

    schema = tool.get("input_schema", {}) or {}
    try:
        validate(input_data or {}, schema)
    except Exception as e:
        return {"error": str(e)}

    # Local python handler
    handler = tool.get("handler")
    if handler and callable(handler):
        try:
            return handler(input_data or {})
        except Exception as e:
            return {"error": str(e)}

    # Remote HTTP endpoint
    endpoint = tool.get("endpoint")
    if endpoint:
        method = tool.get("method", "POST").upper()
        headers = tool.get("headers")
        try:
            if method == "GET":
                resp = requests.get(endpoint, params=input_data, headers=headers, timeout=10)
            else:
                resp = requests.request(method, endpoint, json=input_data, headers=headers, timeout=10)
            resp.raise_for_status()
            try:
                return resp.json()
            except Exception:
                return {"result": resp.text}
        except Exception as e:
            return {"error": str(e)}

    return {"error": "No valid execution method for tool"}