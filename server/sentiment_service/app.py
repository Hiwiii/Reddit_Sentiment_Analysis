from flask import Flask, jsonify, request
from dotenv import load_dotenv
import os

# ✅ import the local file directly
from logic import analyze_posts, quick_db_check

environment = os.getenv("FLASK_ENV", "development")
load_dotenv(".env.production" if environment == "production" else ".env.local")

app = Flask(__name__)

@app.route("/ping", methods=["GET"])
def ping():
    ok, total = quick_db_check()
    return jsonify({"message": "Sentiment Service Pong!", "db": "ok" if ok else "fail", "total_posts": total}), 200

@app.route("/analyze", methods=["GET"])
def get_sentiment_analysis():
    try:
        limit = request.args.get("limit", default=50, type=int)
        subreddit = request.args.get("subreddit", default=None, type=str)
        results, meta = analyze_posts(limit=limit, subreddit=subreddit)
        return jsonify({"message": "Sentiment analysis completed!", "meta": meta, "results": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
