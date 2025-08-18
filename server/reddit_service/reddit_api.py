import os
import requests
import json
from dotenv import load_dotenv, set_key

# 🔍 Load Environment Variables
env_path = os.path.join(os.path.dirname(__file__), ".env.production" if os.getenv("FLASK_ENV") == "production" else ".env.local")
load_dotenv(env_path)

# 🌍 Reddit API Credentials
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
USER_AGENT = os.getenv("USER_AGENT")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
TOKEN_URL = "https://www.reddit.com/api/v1/access_token"

# Storage Service URL
STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://localhost:5006/store-posts")

# Load subreddit categories
with open('config/subreddits.json') as f:
    SUBREDDITS = json.load(f)

def refresh_access_token():
    """Refresh the access token using the refresh token."""
    global ACCESS_TOKEN
    if not REFRESH_TOKEN:
        print("❌ No refresh token available.")
        return None

    print("🔄 Refreshing access token using refresh token...")
    auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
    }
    headers = {"User-Agent": USER_AGENT}

    response = requests.post(TOKEN_URL, auth=auth, data=data, headers=headers)

    if response.status_code == 200:
        ACCESS_TOKEN = response.json().get("access_token")
        set_key(env_path, "ACCESS_TOKEN", ACCESS_TOKEN)  # ✅ Save new access token in .env
        print("✅ Access token refreshed and stored!")
        return ACCESS_TOKEN
    else:
        print(f"❌ Failed to refresh access token: {response.status_code}, {response.json()}")
        return None

def make_authenticated_request(url):
    """Make an authenticated request to Reddit API."""
    global ACCESS_TOKEN

    if not ACCESS_TOKEN:
        print("🔄 No access token found. Using stored token...")
        ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "User-Agent": USER_AGENT
    }
    response = requests.get(url, headers=headers)

    # If token expired, refresh it and retry
    if response.status_code == 401:
        print("🔄 Access token expired. Refreshing...")
        ACCESS_TOKEN = refresh_access_token()
        if ACCESS_TOKEN:
            headers["Authorization"] = f"Bearer {ACCESS_TOKEN}"
            response = requests.get(url, headers=headers)
        else:
            return {"error": "Failed to refresh access token"}

    return response.json() if response.status_code == 200 else {"error": "Failed to fetch data", "status_code": response.status_code}

def fetch_top_posts(subreddit, limit=20):
    """Fetch top posts from a specific subreddit."""
    print(f"🔍 Fetching top {limit} posts from r/{subreddit}...")
    url = f"https://oauth.reddit.com/r/{subreddit}/top?limit={limit}"
    posts = make_authenticated_request(url)
    return posts

def send_to_storage_service(data):
    """Send fetched posts to storage service."""
    try:
        print("📤 Sending data to storage service...")
        print(json.dumps(data, indent=2))  # Debugging: Print what is being sent

        response = requests.post(STORAGE_SERVICE_URL, json=data)
        if response.status_code == 201:
            print("🚀 Successfully stored posts in storage service!")
        else:
            print(f"❌ Failed to store posts: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"❌ Error connecting to storage service: {e}")

def fetch_all_subreddits():
    """Fetch top posts from all predefined subreddits and store them."""
    all_posts = {}
    for category, subreddits in SUBREDDITS.items():
        all_posts[category] = {}
        for subreddit in subreddits:
            posts = fetch_top_posts(subreddit)
            all_posts[category][subreddit] = posts
    
    # ✅ Debugging: Print the fetched posts before sending
    print("📥 FETCHED POSTS (before sending to storage):")
    print(json.dumps(all_posts, indent=2))  

    # ✅ Debugging: Check if `send_to_storage_service()` is even being called
    print("📤 SENDING TO STORAGE...")
    send_to_storage_service(all_posts)

    return all_posts

if __name__ == "__main__":
    all_fetched_posts = fetch_all_subreddits()
    print("🚀 Successfully fetched and stored posts from all subreddits!")
