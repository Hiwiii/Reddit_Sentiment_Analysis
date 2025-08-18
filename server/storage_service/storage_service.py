from flask import Flask, request, jsonify
import os
from mongoengine import Document, StringField, IntField, BooleanField, DateTimeField
from dotenv import load_dotenv
import database  # ✅ Import database.py to handle the MongoDB connection
from datetime import datetime

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env.production" if os.getenv("FLASK_ENV") == "production" else ".env.local"))

app = Flask(__name__)

# ✅ Define the Post document model
class Post(Document):
    post_id = StringField(required=True, unique=True)
    title = StringField()
    author = StringField()
    subreddit = StringField()
    score = IntField()
    num_comments = IntField()
    created_utc = DateTimeField()
    url = StringField()
    is_video = BooleanField()

@app.route("/store-posts", methods=["POST"])
def store_posts():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # ✅ Insert posts into MongoDB
        for category, subreddits in data.items():
            for subreddit, posts in subreddits.items():
                for post in posts.get("data", {}).get("children", []):
                    post_data = post["data"]

                    from datetime import datetime
                    created_utc = post_data.get("created_utc")
                    created_utc_dt = datetime.utcfromtimestamp(created_utc) if created_utc else None

                    Post.objects(post_id=post_data["id"]).update_one(
                        set__title=post_data.get("title"),
                        set__author=post_data.get("author"),
                        set__subreddit=post_data.get("subreddit"),
                        set__score=post_data.get("score"),
                        set__num_comments=post_data.get("num_comments"),
                        set__created_utc=created_utc_dt,
                        set__url=post_data.get("url"),
                        set__is_video=post_data.get("is_video"),
                        upsert=True
                    )

        return jsonify({"message": "Posts stored successfully!"}), 201

    except Exception as e:
        print(f"❌ Error storing posts: {e}")
        return jsonify({"error": "Failed to store posts", "details": str(e)}), 500


@app.route("/ping", methods=["GET"])
def ping():
    """Health check endpoint"""
    return jsonify({"message": "Storage Service Pong!"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006, debug=True)
