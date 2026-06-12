import os
from urllib.parse import urlparse

try:
    from pymongo import MongoClient
except Exception:
    MongoClient = None

MONGO_URL = os.environ.get('DB_URL') or os.environ.get('MONGO_URL') or 'mongodb://localhost:27017/mcp_db'


def _get_client():
    if MongoClient is None:
        raise RuntimeError('pymongo is not installed')
    return MongoClient(MONGO_URL)


def _get_db():
    client = _get_client()
    # try to get db from URL path
    parsed = urlparse(MONGO_URL)
    dbname = parsed.path.lstrip('/') if parsed.path else 'mcp_db'
    if not dbname:
        dbname = 'mcp_db'
    return client[dbname]


def init_db(seed=True, sample_qas=None):
    db = _get_db()
    coll = db.qa
    if seed:
        if coll.count_documents({}) == 0:
            if sample_qas is None:
                sample_qas = [
                    ("What is MCP?", "MCP stands for Model/Tool Composition Platform."),
                    ("How to run the server?", "Use uvicorn mcp_server.server:app --port 8000"),
                ]
            docs = []
            for q, a in sample_qas:
                docs.append({"question": q, "answer": a, "tags": None})
            coll.insert_many(docs)


def db_status():
    db = _get_db()
    coll = db.qa
    try:
        cnt = coll.count_documents({})
    except Exception:
        cnt = None
    return {'db_url': MONGO_URL, 'rows': cnt}


def search(query, limit=5):
    db = _get_db()
    coll = db.qa
    if not query:
        return []
    regex = {"$regex": query, "$options": 'i'}
    cursor = coll.find({"$or": [{"question": regex}, {"answer": regex}]}, {"question": 1, "answer": 1}).limit(limit)
    results = []
    for doc in cursor:
        results.append({"id": str(doc.get('_id')), "question": doc.get('question'), "answer": doc.get('answer')})
    return results
                        
                     