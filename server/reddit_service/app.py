from flask import Flask, jsonify
from reddit_service import fetch_top_posts
from dotenv import load_dotenv
import os

# Determine if we're in local or production
environment = os.getenv("FLASK_ENV", "development")

if environment == "production":
    load_dotenv(".env.production")
else:
    load_dotenv(".env.local")

app = Flask(__name__)


@app.route("/reddit-posts/<subreddit>", methods=["GET"])
def get_reddit_posts(subreddit):
    try:
        posts = fetch_top_posts(subreddit)
        return jsonify(posts), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
