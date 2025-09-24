# server/app.py
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

# --- Local-only: load .env files if present (won't override EB env vars) ---
try:
    from dotenv import load_dotenv
    if os.path.exists(".env.local"):
        load_dotenv(".env.local", override=False)
    if os.path.exists(".env.production"):
        load_dotenv(".env.production", override=False)
except Exception:
    pass

from flask import Flask, jsonify
from werkzeug.middleware.dispatcher import DispatcherMiddleware

# Import the three Flask apps
from reddit_service.app import app as reddit_app
from sentiment_service.app import app as sentiment_app
from storage_service.app import app as storage_app

# Small root app
_root = Flask(__name__)

@_root.get("/")
def home():
    return jsonify(
        status="ok",
        message="Reddit Sentiment Analysis API is running ✅",
        env=os.getenv("FLASK_ENV", "unknown")
    ), 200

@_root.get("/health")
def health():
    return "OK", 200

# WSGI entrypoint for Elastic Beanstalk
application = DispatcherMiddleware(_root, {
    "/reddit": reddit_app,
    "/sentiment": sentiment_app,
    "/storage": storage_app,
})
