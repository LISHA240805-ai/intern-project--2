import json
import os
import importlib.util

BASE_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, os.pardir))
TOOLS_DIR = os.path.join(ROOT_DIR, "tools")
ADAPTERS_DIR = os.path.join(BASE_DIR, "adapters")


def load_tools():
    tools = {}

    # Load JSON tool descriptors from /tools
    if os.path.isdir(TOOLS_DIR):
        for fname in os.listdir(TOOLS_DIR):
            path = os.path.join(TOOLS_DIR, fname)
            if not fname.lower().endswith(".json"):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    tool = json.load(f)
                    tools[tool["tool_name"]] = tool
            except Exception:
                continue

    # Load local python adapters from mcp_server/adapters
    if os.path.isdir(ADAPTERS_DIR):
        for fname in os.listdir(ADAPTERS_DIR):
            if not fname.lower().endswith(".py"):
                continue
            path = os.path.join(ADAPTERS_DIR, fname)
            name = os.path.splitext(fname)[0]
            try:
                spec = importlib.util.spec_from_file_location(f"mcp_server.adapters.{name}", path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)

                # adapter can expose TOOL dict and a handler function
                tool_meta = getattr(mod, "TOOL", None)
                handler = getattr(mod, "handler", None) or getattr(mod, "handle", None)
                if tool_meta and "tool_name" in tool_meta:
                    tool_meta = dict(tool_meta)
                    if handler:
                        tool_meta["handler"] = handler
                    tools[tool_meta["tool_name"]] = tool_meta
            except Exception:
                continue

    return tools


REGISTRY = load_tools()


def get_registry():
    global REGISTRY
    return REGISTRY


def reload_registry():
    """Reload tools from disk and adapters, returning the new registry."""
    global REGISTRY
    REGISTRY = load_tools()
    return REGISTRY
