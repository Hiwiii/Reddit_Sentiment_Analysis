from mongoengine import connect, Document, StringField
from transformers import pipeline
import os

# Don’t connect or load pipeline at import time!
# Instead, lazy-initialize inside a function.

class RedditPost(Document):
    title = StringField(required=True)
    body = StringField()

_sentiment_analyzer = None
_db_connected = False

def get_sentiment_analyzer():
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="nlptown/bert-base-multilingual-uncased-sentiment"
        )
    return _sentiment_analyzer

def ensure_db():
    global _db_connected
    if not _db_connected:
        MONGO_URI = os.getenv("MONGODB_URI", "mongodb://mongodb:27017/reddit_sa")
        connect(db="reddit_sentiment", host=MONGO_URI, alias="default")
        _db_connected = True

def analyze_posts():
    """Fetch Reddit posts from MongoDB and analyze their sentiment."""
    ensure_db()
    posts = RedditPost.objects.only("title", "body")

    analyzer = get_sentiment_analyzer()
    results = []
    for post in posts:
        text = f"{post.title} {post.body or ''}"
        analysis = analyzer(text)[0]
        results.append(
            {"title": post.title, "label": analysis["label"], "score": analysis["score"]}
        )
    return results
