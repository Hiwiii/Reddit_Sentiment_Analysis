from mongoengine import connect
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(".env.production" if os.getenv("FLASK_ENV") == "production" else ".env.local")

# Connect to MongoDB using MongoEngine
connect(
    db="reddit_sentiment",
    host=os.getenv("MONGODB_URI"),
    alias="default"
)
