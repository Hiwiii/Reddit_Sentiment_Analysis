from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv

# Load env first (prod vs local)
load_dotenv(os.path.join(
    os.path.dirname(__file__),
    ".env.production" if os.getenv("FLASK_ENV") == "production" else ".env.local"
))

import database  # establishes Mongo connection via MONGODB_URI
from storage_service import (
    Post,
    upsert_posts,
    get_recent_posts,
    upsert_sentiment,     # <-- use this
)

app = Flask(__name__)

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"message": "Storage Service Pong!"}), 200

@app.route("/store-posts", methods=["POST"])
def store_reddit_posts():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No data provided"}), 400
    try:
        count = upsert_posts(data)
        return jsonify({"message": "Posts stored successfully!", "count": count}), 201
    except Exception as e:
        print(f"❌ Error storing posts: {e}")
        return jsonify({"error": "Failed to store posts", "details": str(e)}), 500

@app.route("/posts/recent", methods=["GET"])
def recent_posts():
    try:
        limit = int(request.args.get("limit", 20))
        subreddit = request.args.get("subreddit")
        data = get_recent_posts(limit=limit, subreddit=subreddit)
        return jsonify(data), 200
    except Exception as e:
        print(f"❌ Error reading posts: {e}")
        return jsonify({"error": "Failed to read posts", "details": str(e)}), 500

@app.route("/posts/pending", methods=["GET"])
def posts_pending():
    try:
        limit = max(1, min(int(request.args.get("limit", 50)), 200))
        subreddit = request.args.get("subreddit")

        q = Post.objects(sentiment_polarity__exists=False)  # no sentiment yet
        if subreddit:
            q = q.filter(subreddit__iexact=subreddit)

        posts = q.order_by("-created_utc")[:limit]
        data = [
            {"post_id": p.post_id, "title": p.title, "subreddit": p.subreddit}
            for p in posts if p.title
        ]
        return jsonify({"count": len(data), "posts": data}), 200
    except Exception as e:
        print(f"❌ Error listing pending posts: {e}")
        return jsonify({"error": "Failed to list pending posts", "details": str(e)}), 500

@app.route("/store-sentiment", methods=["POST"])
def store_sentiment():
    payload = request.get_json(silent=True) or {}
    results = payload.get("results") or []
    try:
        count = upsert_sentiment(results)   # <-- call it here
        return jsonify({"message": "Sentiment stored", "count": count}), 201
    except Exception as e:
        print(f"❌ Error storing sentiment: {e}")
        return jsonify({"error": "Failed to store sentiment", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
