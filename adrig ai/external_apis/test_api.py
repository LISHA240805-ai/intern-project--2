"""Example external API used to demonstrate MCP integration.

Endpoints:
- POST /flights  -> expects JSON {"from": "A", "to": "B"}
- POST /echo     -> expects JSON {"message": "..."}
- GET  /status   -> health check
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Example External API")


class FlightsRequest(BaseModel):
    from_: str
    to: str


@app.post("/flights")
def flights(payload: dict):
    try:
        origin = payload.get("from") or payload.get("from_")
        dest = payload.get("to")
        if not origin or not dest:
            raise ValueError("'from' and 'to' are required")
        return {"flights": [{"from": origin, "to": dest, "price": 5000}]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/echo")
def echo(payload: dict):
    msg = payload.get("message")
    if msg is None:
        raise HTTPException(status_code=400, detail="'message' is required")
    return {"echo": msg}


@app.get("/status")
def status():
    return {"status": "ok"}
