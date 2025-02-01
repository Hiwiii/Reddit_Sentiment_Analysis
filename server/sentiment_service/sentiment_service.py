from pymongo import MongoClient
from transformers import pipeline
import os


# Initialize MongoDB client
def get_mongo_client():
    MONGO_URI = os.getenv("MONGODB_URI")
    return MongoClient(MONGO_URI)


# Set up Hugging Face sentiment analysis pipeline
sentiment_analyzer = pipeline(
    "sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment"
)


def analyze_posts():
    """Fetch Reddit posts from MongoDB and analyze their sentiment."""
    client = get_mongo_client()
    db = client.reddit_sentiment
    posts = list(db.posts.find({}, {"_id": 0, "title": 1, "body": 1}))

    results = []
    for post in posts:
        text = f"{post.get('title', '')} {post.get('body', '')}"
        analysis = sentiment_analyzer(text)[0]
        results.append(
            {
                "title": post.get("title", ""),
                "label": analysis["label"],
                "score": analysis["score"],
            }
        )

    return results
