from flask import Flask, jsonify, request, redirect
from reddit_api import make_authenticated_request, fetch_all_subreddits
from dotenv import load_dotenv, set_key
import random
import string
import os
import requests

# Load Environment Variables
environment = os.getenv("FLASK_ENV", "development")
env_file = ".env.production" if environment == "production" else ".env.local"
load_dotenv(env_file)

STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
USER_AGENT = os.getenv("USER_AGENT")
TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
AUTH_URL = "https://www.reddit.com/api/v1/authorize"

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")

app = Flask(__name__)

# Generate a random state string
STATE = "".join(random.choices(string.ascii_letters + string.digits, k=16))


@app.route("/authorize")
def authorize():
    """Redirect the user to Reddit's OAuth login page."""
    auth_url = (
        f"https://www.reddit.com/api/v1/authorize?"
        f"client_id={CLIENT_ID}&response_type=code&state={STATE}&"
        f"redirect_uri={REDIRECT_URI}&duration=permanent&scope=read"
    )
    return redirect(auth_url)


@app.route("/callback")
def callback():
    global ACCESS_TOKEN
    auth_code = request.args.get("code")

    if not auth_code:
        return jsonify({"error": "Authorization code missing"}), 400

    # Exchange authorization code for access and refresh tokens
    auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    data = {"grant_type": "authorization_code", "code": auth_code, "redirect_uri": REDIRECT_URI}
    headers = {"User-Agent": USER_AGENT}

    response = requests.post(TOKEN_URL, auth=auth, data=data, headers=headers)

    if response.status_code == 200:
        token_data = response.json()
        ACCESS_TOKEN = token_data.get("access_token")
        REFRESH_TOKEN = token_data.get("refresh_token")

        # Debug: Confirm the tokens are received
        print(f"✅ Access Token received: {ACCESS_TOKEN[:20]}...")  # Truncated for readability
        print(f"✅ Refresh Token received: {REFRESH_TOKEN}")

        # Save the tokens to .env.local
        set_key(env_file, "ACCESS_TOKEN", ACCESS_TOKEN)
        print("✅ Access token saved to .env.local")

        if REFRESH_TOKEN:
            set_key(env_file, "REFRESH_TOKEN", REFRESH_TOKEN)
            print("✅ Refresh token saved to .env.local")
        else:
            print("❌ No refresh token to save.")

        # Verify the env file path
        print(f"🔍 Saving tokens to: {env_file}")

        return jsonify({"message": "OAuth Success", "access_token": ACCESS_TOKEN, "refresh_token": REFRESH_TOKEN})
    else:
        print(f"❌ Failed to obtain access token: {response.status_code}, {response.json()}")
        return jsonify({"error": "Failed to obtain access token", "details": response.json()}), 401


@app.route("/reddit-posts", methods=["GET"])
def get_reddit_posts():
    """Fetch top posts from a given subreddit and persist them via storage_service."""
    subreddit = request.args.get("subreddit", "python")
    limit = request.args.get("limit", 20)

    url = f"https://oauth.reddit.com/r/{subreddit}/top?limit={limit}"
    posts = make_authenticated_request(url)  # Reddit API response (Listing)

    # --- NEW: forward to storage_service for persistence ---
    stored = None
    if STORAGE_SERVICE_URL:
        try:
            r = requests.post(STORAGE_SERVICE_URL, json=posts, timeout=10)
            r.raise_for_status()
            stored = r.json()
        except Exception as e:
            # Don't fail the fetch just because storing failed
            print(f"❌ Failed to store posts via storage_service: {e}")
    # -------------------------------------------------------

    return jsonify({"data": posts, "store_result": stored}), 200


@app.route("/fetch-all", methods=["GET"])
def fetch_all():
    """Fetch top posts from all predefined subreddits."""
    posts = fetch_all_subreddits()
    return jsonify(posts), 200


@app.route("/ping", methods=["GET"])
def ping():
    """Health check endpoint."""
    return jsonify({"message": "Reddit Service Pong!"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5008, debug=True)
