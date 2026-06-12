"""DB wrapper selecting appropriate backend (SQLAlchemy or MongoDB)."""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

DB_URL = os.environ.get('DB_URL')
DB_TYPE = os.environ.get('DB_TYPE')


def _choose_backend():
    # If DB_TYPE explicitly set
    if DB_TYPE:
        if DB_TYPE.lower() in ('mongo', 'mongodb'):
            return 'mongo'
        return 'sql'

    # Infer from DB_URL
    if DB_URL and (DB_URL.startswith('mongodb://') or DB_URL.startswith('mongodb+srv://')):
        return 'mongo'
    return 'sql'


_backend = None


def _load_backend():
    global _backend
    if _backend is not None:
        return _backend
    kind = _choose_backend()
    if kind == 'mongo':
        from mcp_server import db_mongo_backend as backend
    else:
        from mcp_server import db_sql_backend as backend
    _backend = backend
    return _backend


def init_db(seed=True, sample_qas=None):
    backend = _load_backend()
    return backend.init_db(seed=seed, sample_qas=sample_qas)


def db_status():
    backend = _load_backend()
    return backend.db_status()


def search(query, limit=5):
    backend = _load_backend()
    return backend.search(query, limit)
*** End Patch