TOOL = {
    "tool_name": "local_echo",
    "input_schema": {"required": ["message"]},
    "description": "Simple local echo adapter"
}


def handler(input_data):
    """Return a simple echo response."""
    return {"echo": input_data.get("message")}
