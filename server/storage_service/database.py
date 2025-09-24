# server/storage_service/database.py
import os
from mongoengine import connect

_conn = None

def init_db():
    """Connect lazily; never crash Gunicorn on failure."""
    global _conn
    if _conn:
        return _conn

    uri = os.getenv("MONGODB_URI")
    if not uri:
        print("⚠️  MONGODB_URI not set; starting without DB", flush=True)
        return None

    try:
        _conn = connect(
            host=uri,
            alias="default",
            tls=True,                          # fine for Atlas SRV URIs
            serverSelectionTimeoutMS=5000,     # fail fast on bad network
        )
        # Ping to log a clear success/failure
        _conn.admin.command("ping")
        print("✅ MongoDB connected", flush=True)
    except Exception as e:
        print(f"❌ MongoDB init failed: {e}", flush=True)
        _conn = None
    return _conn
