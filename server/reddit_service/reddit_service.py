import praw
import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request

# Load environment variables based on environment
load_dotenv(
    ".env.production" if os.getenv("FLASK_ENV") == "production" else ".env.local"
)

app = Flask(__name__)


def get_reddit_client():
    """Initialize the Reddit API client with credentials from environment variables."""
    return praw.Reddit(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        username=os.getenv("REDDIT_USERNAME"),
        password=os.getenv("REDDIT_PASSWORD"),
        user_agent=os.getenv("USER_AGENT"),
    )


def fetch_top_posts(subreddit, limit=5):
    """Fetch top posts from a given subreddit and return them as a list of dictionaries."""
    reddit = get_reddit_client()
    posts = [
        {"title": submission.title, "score": submission.score, "url": submission.url}
        for submission in reddit.subreddit(subreddit).hot(limit=limit)
    ]
    return posts


# Flask route to fetch and display top posts
@app.route("/fetch_posts", methods=["GET"])
def fetch_posts():
    subreddit = request.args.get("subreddit", "all")
    limit = int(request.args.get("limit", 5))
    try:
        posts = fetch_top_posts(subreddit, limit)
        return jsonify({"posts": posts}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Ping route to check service availability
@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"message": "Reddit Service Pong!"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=(os.getenv("FLASK_ENV") != "production"))
