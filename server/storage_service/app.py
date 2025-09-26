# server/storage_service/app.py
import os
from flask import Flask, request, jsonify

# DO NOT import init_db or use before_first_request.
# __init__.py already called _db.init_db() when the package was imported.
from .storage_service import (
    Post,
    upsert_posts,
    get_recent_posts,
    upsert_sentiment,
)

app = Flask(__name__)

@app.route("/")
def root():
    return jsonify({"ok": True}), 200

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
        print(f"❌ Error storing posts: {e}", flush=True)
        return jsonify({"error": "Failed to store posts", "details": str(e)}), 500

@app.route("/posts/recent", methods=["GET"])
def recent_posts():
    try:
        limit = int(request.args.get("limit", 20))
        subreddit = request.args.get("subreddit")
        data = get_recent_posts(limit=limit, subreddit=subreddit)
        return jsonify(data), 200
    except Exception as e:
        print(f"❌ Error reading posts: {e}", flush=True)
        return jsonify({"error": "Failed to read posts", "details": str(e)}), 500

@app.route("/posts/pending", methods=["GET"])
def posts_pending():
    try:
        limit = max(1, min(int(request.args.get("limit", 50)), 200))
        subreddit = request.args.get("subreddit")

        q = Post.objects(sentiment_polarity__exists=False)
        if subreddit:
            q = q.filter(subreddit__iexact=subreddit)

        posts = q.order_by("-created_utc")[:limit]
        data = [
            {"post_id": p.post_id, "title": p.title, "subreddit": p.subreddit}
            for p in posts if p.title
        ]
        return jsonify({"count": len(data), "posts": data}), 200
    except Exception as e:
        print(f"❌ Error listing pending posts: {e}", flush=True)
        return jsonify({"error": "Failed to list pending posts", "details": str(e)}), 500

@app.route("/store-sentiment", methods=["POST"])
def store_sentiment():
    payload = request.get_json(silent=True) or {}
    results = payload.get("results") or []
    try:
        count = upsert_sentiment(results)
        return jsonify({"message": "Sentiment stored", "count": count}), 201
    except Exception as e:
        print(f"❌ Error storing sentiment: {e}", flush=True)
        return jsonify({"error": "Failed to store sentiment", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
