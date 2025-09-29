# server/storage_service/app.py
import os
from flask import Flask, request, jsonify
from datetime import datetime, timedelta


from .database import init_db
from .storage_service import (
    Post,
    upsert_posts,
    get_recent_posts,
    upsert_sentiment,
)

app = Flask(__name__)

# Initialize MongoDB once when the module loads (idempotent + non-fatal).
try:
    init_db()
except Exception as e:
    print(f"⚠️ DB init warning: {e}", flush=True)

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

@app.route("/summary", methods=["GET"])
def summary():
    """
    Quick snapshot:
      - counts by polarity (positive/neutral/negative)
      - total/analyzed/pending
      - average VADER compound
    Optional filters:
      ?subreddit=<name>&hours=<lookback_hours>
    """
    try:
        subreddit = request.args.get("subreddit")
        hours_str = request.args.get("hours")

        q = Post.objects
        if subreddit:
            q = q.filter(subreddit__iexact=subreddit)

        lookback_hours = None
        if hours_str:
            try:
                lookback_hours = int(hours_str)
                since = datetime.utcnow() - timedelta(hours=lookback_hours)
                q = q.filter(created_utc__gte=since)
            except Exception:
                lookback_hours = None  # ignore bad value

        total = q.count()
        analyzed_q = q.filter(sentiment_compound__exists=True)
        analyzed = analyzed_q.count()
        pending = q.filter(sentiment_polarity__exists=False).count()

        by_polarity = {
            "positive": q.filter(sentiment_polarity="positive").count(),
            "neutral":  q.filter(sentiment_polarity="neutral").count(),
            "negative": q.filter(sentiment_polarity="negative").count(),
        }

        compounds = [
            p.sentiment_compound
            for p in analyzed_q.only("sentiment_compound")
            if p.sentiment_compound is not None
        ]
        avg_compound = (sum(compounds) / len(compounds)) if compounds else None

        return jsonify({
            "filters": {"subreddit": subreddit, "hours": lookback_hours},
            "counts": {
                "total": total,
                "analyzed": analyzed,
                "pending": pending,
                "by_polarity": by_polarity,
            },
            "average_compound": avg_compound,
        }), 200
    except Exception as e:
        print(f"❌ Error building summary: {e}", flush=True)
        return jsonify({"error": "Failed to build summary", "details": str(e)}), 500
