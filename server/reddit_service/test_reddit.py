import os
import praw
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")

# Reddit API Credentials
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
USERNAME = os.getenv("REDDIT_USERNAME")
PASSWORD = os.getenv("REDDIT_PASSWORD")
USER_AGENT = os.getenv("USER_AGENT", "my-reddit-app/0.1")

# Initialize praw
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    username=USERNAME,
    password=PASSWORD,
    user_agent=USER_AGENT
)

# Check if praw is authenticated
print("✅ Reddit authentication successful!")
print(f"🔑 Authenticated User: {reddit.user.me()}")  # Debugging: Check login


# curl -X POST -d 'grant_type=password&username=Eastern-Web-7645&password=NhNQMZat49n!' \
#    --user "xAK7DW0WPbAUe8p6ZgXT1w:wLpH5hnMbDEopSlo3CGzyd-BMgWngQ" \
#     -H "User-Agent: my-reddit-app/0.1" \
#     "https://www.reddit.com/api/v1/access_token"
