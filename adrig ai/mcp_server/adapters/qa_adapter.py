from mcp_server import db as mcp_db

TOOL = {
    "tool_name": "qa_search",
    "input_schema": {"required": ["query"]},
    "description": "Searches QA database for relevant answers"
}


def handler(   input_data):
    query = (input_data or {}).get("query", "")
    limit = int((input_data or {}).get("limit", 5))
    try:
        results = mcp_db.search(query, limit=limit)
        return {"query": query, "results": results}
    except Exception as e:
        return {"error": str(e)}
