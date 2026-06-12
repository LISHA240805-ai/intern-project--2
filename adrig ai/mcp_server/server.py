from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import registry
from engine import execute
import db_init
from mcp_server import db as mcp_db

load_dotenv()

app = FastAPI(title="MCP Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExecuteRequest(BaseModel):
    tool_name: str
    input: dict = {}


@app.post("/mcp/execute")
def mcp_execute(req: ExecuteRequest):
    res = execute(req.tool_name, req.input)
    if isinstance(res, dict) and res.get("error"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res


@app.get("/mcp/tools")
def list_tools():
    tools = registry.get_registry()
    result = []
    for name, meta in tools.items():
        entry = {"tool_name": name}
        for k in ("description", "input_schema", "endpoint", "method"):
            if k in meta:
                entry[k] = meta[k]
        result.append(entry)
    return {"tools": result}


@app.get("/mcp/tools/{tool_name}")
def describe_tool(tool_name: str):
    tools = registry.get_registry()
    tool = tools.get(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


@app.post("/mcp/reload")
def reload_tools():
    tools = registry.reload_registry()
    return {"reloaded": len(tools)}


@app.get("/mcp/health")
def health():
    return {"status": "ok"}

@app.post("/mcp/db/init")
def mcp_db_init(seed: bool = True):
    try:
        db_init.create_db(seed=seed)
        return {"status": "ok", "message": "DB initialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/db/status")
def mcp_db_status():
    try:
        status = mcp_db.db_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("mcp_server.server:app", host="0.0.0.0", port=8000, reload=False)