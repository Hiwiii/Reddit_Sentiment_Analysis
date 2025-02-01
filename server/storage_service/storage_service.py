from flask import Flask, jsonify, request
from mongoengine import Document, StringField, connect
from dotenv import load_dotenv
import os

app = Flask(__name__)

load_dotenv(
    ".env.production" if os.getenv("FLASK_ENV") == "production" else ".env.local"
)
MONGO_URI = os.getenv("MONGODB_URI")

connect(db="reddit_sentiment", host=MONGO_URI, alias="default")


class TestData(Document):
    title = StringField(required=True)
    body = StringField()


def store_post(data):
    """Store Reddit post data in MongoDB."""
    post = TestData(title=data.get("title"), body=data.get("body"))
    post.save()
    return post.id


@app.route("/test-db-connection", methods=["GET"])
def test_db_connection():
    try:
        collections = connect().list_collection_names()
        return (
            jsonify(
                {
                    "message": "MongoDB connection successful!",
                    "collections": collections,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
