# reddit_service/reddit_api.py
import os
import json
from pathlib import Path
import requests

# ──────────────────────────────────────────────────────────────────────────────
# Reddit / App configuration (read only from environment)
# ──────────────────────────────────────────────────────────────────────────────
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
USER_AGENT = os.getenv("USER_AGENT") or "reddit-sentiment-app/0.1"
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
TOKEN_URL = "https://www.reddit.com/api/v1/access_token"

# Storage service base:
#   • EB (single env):  STORAGE_BASE_URL=http://127.0.0.1:8000/storage
#   • Public domain:    STORAGE_BASE_URL=http://<your-eb-domain>/storage
#   • Local/Docker:     defaults to http://storage_service:5002
STORAGE_BASE = os.getenv("STORAGE_BASE_URL", "http://storage_service:5002")

def _svc_url(path: str) -> str:
    return f"{STORAGE_BASE.rstrip('/')}/{path.lstrip('/')}"

STORE_POSTS_URL = _svc_url("/store-posts")

# ──────────────────────────────────────────────────────────────────────────────
# subreddits.json loader (robust; won’t crash if missing)
# ──────────────────────────────────────────────────────────────────────────────
def _load_subreddit_catalog():
    """
    Locate and parse subreddits JSON from common places, but never crash if it's
    missing. Always return {category: [subreddit, ...]}.
    """
    here = Path(__file__).resolve().parent

    override = os.getenv("SUBREDDITS_JSON")
    candidates = []
    if override:
        candidates.append(Path(override))

    candidates += [
        here / "config" / "subreddits.json",                # reddit_service/config/subreddits.json
        here.parent / "config" / "subreddits.json",         # server/config/subreddits.json
        Path.cwd() / "config" / "subreddits.json",
    ]

    for p in candidates:
        if p.exists():
            try:
                with p.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                if isinstance(data, dict):
                    if "subreddits" in data and isinstance(data["subreddits"], list):
                        catalog = {"default": data["subreddits"]}
                    elif all(isinstance(v, list) for v in data.values()):
                        catalog = data
                    else:
                        raise ValueError("Unsupported dict schema in subreddits.json")
                elif isinstance(data, list):
                    catalog = {"default": data}
                else:
                    raise ValueError("subreddits.json must be a dict or a list")

                total = sum(len(v) for v in catalog.values())
                print(f"✅ Loaded {total} subreddits from {p}", flush=True)
                return catalog
            except Exception as e:
                print(f"⚠️ Failed to parse {p}: {e}", flush=True)
                break  # found a file but it's bad; stop searching

    fallback = {"default": ["python", "programming", "technology"]}
    print("⚠️ subreddits.json not found; using fallback:", fallback["default"], flush=True)
    return fallback

SUBREDDITS = _load_subreddit_catalog()

# ──────────────────────────────────────────────────────────────────────────────
# Reddit OAuth helpers (no writing to .env; just logs)
# ──────────────────────────────────────────────────────────────────────────────
def refresh_access_token():
    """Refresh the access token using the refresh token, if available."""
    global ACCESS_TOKEN
    if not REFRESH_TOKEN:
        print("❌ No refresh token available.")
        return None
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ CLIENT_ID/CLIENT_SECRET not configured; cannot refresh token.")
        return None

    print("🔄 Refreshing access token using refresh token...")
    auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    data = {"grant_type": "refresh_token", "refresh_token": REFRESH_TOKEN}
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.post(TOKEN_URL, auth=auth, data=data, headers=headers, timeout=20)
    except Exception as e:
        print(f"❌ Token refresh network error: {e}")
        return None

    if response.status_code == 200:
        ACCESS_TOKEN = response.json().get("access_token")
        print("✅ Access token refreshed.")
        return ACCESS_TOKEN
    else:
        try:
            details = response.json()
        except Exception:
            details = response.text
        print(f"❌ Failed to refresh access token: {response.status_code}, {details}")
        return None

def make_authenticated_request(url):
    """Make an authenticated GET to Reddit API, with auto-refresh on 401."""
    global ACCESS_TOKEN

    if not ACCESS_TOKEN:
        ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

    if not ACCESS_TOKEN:
        return {"error": "No ACCESS_TOKEN configured", "status_code": 401}

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "User-Agent": USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=20)
    except Exception as e:
        return {"error": f"Network error: {e}"}

    if response.status_code == 401:
        print("🔄 Access token expired. Refreshing...")
        new_token = refresh_access_token()
        if new_token:
            headers["Authorization"] = f"Bearer {new_token}"
            try:
                response = requests.get(url, headers=headers, timeout=20)
            except Exception as e:
                return {"error": f"Network error after refresh: {e}"}
        else:
            return {"error": "Failed to refresh access token"}

    return (
        _safe_json(response)
        if response.status_code == 200
        else {"error": "Failed to fetch data", "status_code": response.status_code, "body": _safe_body(response)}
    )

def _safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return {"error": "Invalid JSON from Reddit", "status_code": resp.status_code, "body": resp.text[:500]}

def _safe_body(resp):
    try:
        return resp.json()
    except Exception:
        return resp.text[:1000]

# ──────────────────────────────────────────────────────────────────────────────
# High-level helpers
# ──────────────────────────────────────────────────────────────────────────────
def fetch_top_posts(subreddit, limit=20):
    """Fetch top posts from a specific subreddit."""
    try:
        limit = int(limit)
    except Exception:
        limit = 20
    print(f"🔍 Fetching top {limit} posts from r/{subreddit}...")
    url = f"https://oauth.reddit.com/r/{subreddit}/top?limit={limit}"
    return make_authenticated_request(url)

def send_to_storage_service(data):
    """Send fetched posts to the storage service (non-fatal on failure)."""
    try:
        print(f"📤 Sending data to storage service at {STORE_POSTS_URL} ...")
        r = requests.post(STORE_POSTS_URL, json=data, timeout=30)
        if r.status_code in (200, 201):
            print("🚀 Successfully stored posts in storage service!")
        else:
            print(f"❌ Failed to store posts: {r.status_code}, {_safe_body(r)}")
    except Exception as e:
        print(f"❌ Error connecting to storage service: {e}")

def fetch_all_subreddits():
    """
    Fetch top posts from all predefined subreddits and store them.
    SUBREDDITS is a dict {category: [subs]}.
    """
    all_posts = {}
    for category, subs in SUBREDDITS.items():
        all_posts[category] = {}
        for subreddit in subs:
            posts = fetch_top_posts(subreddit)
            all_posts[category][subreddit] = posts

    print("📤 SENDING TO STORAGE...")
    send_to_storage_service(all_posts)
    return all_posts

if __name__ == "__main__":
    result = fetch_all_subreddits()
    print("🚀 Successfully fetched and attempted to store posts from all subreddits!")
