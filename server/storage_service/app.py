from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv

# Ensure env is loaded (choose local vs production)
load_dotenv(os.path.join(
    os.path.dirname(__file__),
    ".env.production" if os.getenv("FLASK_ENV") == "production" else ".env.local"
))

import database  # establishes connection via MONGODB_URI
from storage_service import upsert_posts, get_recent_posts

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
        return jsonify({"message": f"Posts stored successfully!", "count": count}), 201
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

if __name__ == "__main__":
    # This is the only server we run
    app.run(host="0.0.0.0", port=5002, debug=True)
