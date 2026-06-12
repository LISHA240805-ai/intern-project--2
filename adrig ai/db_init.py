import os
import sqlite3

ROOT = os.path.dirname(__file__)
DATA_DIR = os.path.join(ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "qa.db")

SAMPLE_QAS = [
    ("What is MCP?", "MCP stands for Model/Tool Composition Platform."),
    ("How to run the server?", "Use uvicorn mcp_server.server:app --port 8000"),
    ("Where are tools stored?", "Tools are stored in the tools/ directory as JSON descriptors or adapters in mcp_server/adapters/"),
]

def create_db(seed=True):
    # Prefer SQLAlchemy-backed initialization via mcp_server.db
    try:
        from mcp_server.db import init_db
        init_db(seed=seed, sample_qas=SAMPLE_QAS)
        return
    except Exception:
        # Fallback to local sqlite file creation
        os.makedirs(DATA_DIR, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS qa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                tags TEXT
            )
            """
        )

        # Seed sample data if table empty
        if seed:
            c.execute("SELECT count(1) FROM qa")
            if c.fetchone()[0] == 0:
                c.executemany("INSERT INTO qa (question, answer, tags) VALUES (?, ?, ?)", [(q, a, None) for q, a in SAMPLE_QAS])
                conn.commit()
                print(f"Seeded {len(SAMPLE_QAS)} records into {DB_PATH}")
            else:
                print("DB already seeded")

        conn.close()
        print("DB path:", DB_PATH)


if __name__ == "__main__":
    create_db()
