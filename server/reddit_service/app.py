# server/reddit_service/app.py
import os, random, string, requests
from flask import Flask, jsonify, request, redirect
from .reddit_api import make_authenticated_request, fetch_all_subreddits

STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL")  # e.g. http://127.0.0.1:8000/storage
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
USER_AGENT = os.getenv("USER_AGENT")
TOKEN_URL = "https://www.reddit.com/api/v1/access_token"

# Optional: existing tokens if you’ve set them as env vars
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")

app = Flask(__name__)

@app.route("/")
def root():
    return jsonify({"ok": True}), 200

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"message": "Reddit Service Pong!"}), 200

# Generate a random state string (basic CSRF protection for OAuth)
STATE = "".join(random.choices(string.ascii_letters + string.digits, k=16))

@app.route("/authorize")
def authorize():
    """Redirect the user to Reddit's OAuth login page."""
    auth_url = (
        "https://www.reddit.com/api/v1/authorize?"
        f"client_id={CLIENT_ID}&response_type=code&state={STATE}&"
        f"redirect_uri={REDIRECT_URI}&duration=permanent&scope=read"
    )
    return redirect(auth_url)

@app.route("/callback")
def callback():
    """OAuth redirect handler: exchange code for tokens."""
    global ACCESS_TOKEN, REFRESH_TOKEN

    auth_code = request.args.get("code")
    if not auth_code:
        return jsonify({"error": "Authorization code missing"}), 400

    auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    data = {"grant_type": "authorization_code", "code": auth_code, "redirect_uri": REDIRECT_URI}
    headers = {"User-Agent": USER_AGENT}

    resp = requests.post(TOKEN_URL, auth=auth, data=data, headers=headers)
    if not resp.ok:
        try:
            details = resp.json()
        except Exception:
            details = {"status": resp.status_code, "text": resp.text[:300]}
        return jsonify({"error": "Failed to obtain access token", "details": details}), 401

    token_data = resp.json()
    ACCESS_TOKEN = token_data.get("access_token")
    REFRESH_TOKEN = token_data.get("refresh_token")

    # Make tokens available to this process immediately
    if ACCESS_TOKEN:
        os.environ["ACCESS_TOKEN"] = ACCESS_TOKEN
    if REFRESH_TOKEN:
        os.environ["REFRESH_TOKEN"] = REFRESH_TOKEN

    # Best-effort: only try writing to a local .env file if it exists and is writable (local dev)
    env_file = ".env.local"
    if os.path.exists(env_file) and os.access(env_file, os.W_OK):
        try:
            from dotenv import set_key
            if ACCESS_TOKEN:
                set_key(env_file, "ACCESS_TOKEN", ACCESS_TOKEN)
            if REFRESH_TOKEN:
                set_key(env_file, "REFRESH_TOKEN", REFRESH_TOKEN)
            print(f"✅ Tokens saved to {env_file}", flush=True)
        except Exception as e:
            print(f"⚠️ Could not write tokens to {env_file}: {e}", flush=True)

    return jsonify({"message": "OAuth Success", "token_data": token_data}), 200

@app.route("/reddit-posts", methods=["GET"])
def get_reddit_posts():
    """Fetch top posts from a given subreddit and persist them via storage_service."""
    subreddit = request.args.get("subreddit", "python")
    limit = request.args.get("limit", 20)

    url = f"https://oauth.reddit.com/r/{subreddit}/top?limit={limit}"
    posts = make_authenticated_request(url)  # Reddit API response (Listing)

    # Forward to storage_service for persistence (non-fatal if it fails)
    stored = None
    if STORAGE_SERVICE_URL:
        try:
            r = requests.post(f"{STORAGE_SERVICE_URL}/store-posts", json=posts, timeout=10)
            r.raise_for_status()
            stored = r.json()
        except Exception as e:
            print(f"❌ Failed to store posts via storage_service: {e}", flush=True)

    return jsonify({"data": posts, "store_result": stored}), 200

@app.route("/fetch-all", methods=["GET"])
def fetch_all():
    """Fetch top posts from all predefined subreddits."""
    posts = fetch_all_subreddits()
    return jsonify(posts), 200

if __name__ == "__main__":
    # For standalone local runs, set envs in your shell (CLIENT_ID, etc.)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
