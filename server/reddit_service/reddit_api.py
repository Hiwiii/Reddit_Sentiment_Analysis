import os
import requests
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
