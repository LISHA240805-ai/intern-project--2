import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Text, String, select
from sqlalchemy.exc import OperationalError

DB_URL = os.environ.get('DB_URL') or f"sqlite:///" + os.path.join(os.path.dirname(__file__), '..', 'data', 'qa.db')

metadata = MetaData()
qa_table = Table(
    'qa', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('question', Text, nullable=False),
    Column('answer', Text, nullable=False),
    Column('tags', String(256), nullable=True),
)

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith('sqlite') else {})
    return _engine


def init_db(seed=True, sample_qas=None):
    eng = get_engine()
    try:
        metadata.create_all(eng)
    except OperationalError as e:
        raise

    if seed:
        conn = eng.connect()
        res = conn.execute(qa_table.select().limit(1)).fetchone()
        if res is None:
            from sqlalchemy import insert
            if sample_qas is None:
                sample_qas = [
                    ("What is MCP?", "MCP stands for Model/Tool Composition Platform."),
                    ("How to run the server?", "Use uvicorn mcp_server.server:app --port 8000"),
                    ("Where are tools stored?", "Tools are stored in the tools/ directory as JSON descriptors or adapters in mcp_server/adapters/"),
                ]
            for q, a in sample_qas:
                conn.execute(insert(qa_table).values(question=q, answer=a, tags=None))
            conn.commit()
        conn.close()


def db_status():
    eng = get_engine()
    conn = eng.connect()
    try:
        cnt = conn.execute(select([qa_table.count()])).scalar()
    except Exception:
        cnt = None
    conn.close()
    return {'db_url': DB_URL, 'rows': cnt}


def search(query, limit=5):
    eng = get_engine()
    qtext = "%" + (query or "").replace('%', '') + "%"
    stmt = select([qa_table.c.id, qa_table.c.question, qa_table.c.answer]).where(
        qa_table.c.question.like(qtext) | qa_table.c.answer.like(qtext)
    ).limit(limit)
    conn = eng.connect()
    rows = conn.execute(stmt).fetchall()
    conn.close()
    results = []
    for r in rows:
        results.append({"id": r[0], "question": r[1], "answer": r[2]})
    return results
