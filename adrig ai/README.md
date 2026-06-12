MCP Chatbot Example

This workspace contains a minimal MCP (Tool registry + engine) and example adapters to build a chatbot that:
- Searches a local SQLite QA database
- Uses an LLM adapter (GROQ if `GROQ_API_KEY` is set, otherwise OpenAI or a local fallback) to generate answers
- Serves a simple web frontend that queries the MCP server

Quick start

1) Create virtualenv and install deps

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2) Initialize the database

```bash
python db_init.py
```

3) Run the external example API (optional, used by tools/echo.json)

```bash
uvicorn external_apis.test_api:app --port 8001
```

4) Run the MCP server

```bash
uvicorn mcp_server.server:app --port 8000
```

5) Open the frontend (in a browser) by serving the `web/` folder as static files or opening `web/index.html` and ensure CORS is allowed. For quick test, from the project root run:

```bash
python -m http.server 8080 --directory web
# then open http://localhost:8080
```

Environment

 - To enable real LLM calls, set `GROQ_API_KEY` in your environment before running the MCP server.
 - Optional: set `OPENAI_API_KEY` if you want the adapter to fall back to OpenAI when GROQ is unavailable.

- The system supports any SQL database via the `DB_URL` environment variable (SQLAlchemy URL).
- Examples:
	- SQLite (default): `sqlite:///./data/qa.db`
	- Postgres: `postgresql+psycopg2://user:pass@localhost:5432/mydb`
	- MySQL: `mysql+pymysql://user:pass@localhost:3306/mydb`

Set `DB_URL` before starting the MCP server. If unset, a local SQLite DB at `data/qa.db` is used.

Notes

- Tools are discovered automatically from `tools/*.json` and `mcp_server/adapters/*.py`.
- The frontend calls MCP endpoints: `/mcp/execute` with `tool_name: qa_search` and `tool_name: llm_generate`.
