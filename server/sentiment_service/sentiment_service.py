from mongoengine import connect, Document, StringField
from transformers import pipeline
import os

# ✅ Connect to MongoDB using mongoengine
MONGO_URI = os.getenv("MONGODB_URI")
connect(db="reddit_sentiment", host=MONGO_URI, alias="default")

# ✅ Define the MongoDB Collection Schema using mongoengine
class RedditPost(Document):
    title = StringField(required=True)
    body = StringField()

# ✅ Set up Hugging Face sentiment analysis pipeline
sentiment_analyzer = pipeline(
    "sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment"
)

def analyze_posts():
    """Fetch Reddit posts from MongoDB and analyze their sentiment."""
    posts = RedditPost.objects.only("title", "body")  # Use mongoengine to fetch posts

    results = []
    for post in posts:
        text = f"{post.title} {post.body or ''}"  # Combine title and body
        analysis = sentiment_analyzer(text)[0]
        results.append(
            {
                "title": post.title,
                "label": analysis["label"],
                "score": analysis["score"],
            }
        )

    return results
