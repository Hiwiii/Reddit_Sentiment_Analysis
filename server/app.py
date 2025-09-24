# server/app.py
from flask import Flask, jsonify
from werkzeug.middleware.dispatcher import DispatcherMiddleware

# import your existing Flask apps (unchanged)
from reddit_service.app import app as reddit_app
from sentiment_service.app import app as sentiment_app
from storage_service.app import app as storage_app

# the small root app
_root = Flask(__name__)

@_root.get("/")
def home():
    return jsonify(status="ok",
                   message="Reddit Sentiment Analysis API is running ✅",
                   env="production"), 200

@_root.get("/health")
def health():
    return "OK", 200

# IMPORTANT: Elastic Beanstalk looks for a WSGI callable named `application`
# Mount each service under a path prefix
application = DispatcherMiddleware(_root, {
    "/reddit": reddit_app,
    "/sentiment": sentiment_app,
    "/storage": storage_app,
})
