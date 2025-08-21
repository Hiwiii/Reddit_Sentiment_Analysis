from mongoengine import connect
from dotenv import load_dotenv
import os

# Pick the right env file
env_file = os.path.join(
    os.path.dirname(__file__),
    ".env.production" if os.getenv("FLASK_ENV") == "production" else ".env.local"
)
load_dotenv(env_file)

# Read the full URI from env
MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise ValueError("❌ MONGODB_URI not found in environment variables")

# ✅ Let MongoEngine parse db name from the URI automatically
connect(host=MONGODB_URI, alias="default")
