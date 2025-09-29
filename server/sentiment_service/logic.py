# server/sentiment_service/sentiment_service.py
import os
from datetime import datetime
import requests
import nltk

# VADER import (newer NLTK layout first, fallback to old)
try:
    from nltk.sentiment import SentimentIntensityAnalyzer
except Exception:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer  # type: ignore

# Storage service base:
#   • EB (single env):  STORAGE_BASE_URL=http://127.0.0.1:8000/storage
#   • Public domain:    STORAGE_BASE_URL=http://<your-eb-domain>/storage
#   • Local/Docker:     defaults to http://storage_service:5002
STORAGE_BASE = os.getenv("STORAGE_BASE_URL", "http://storage_service:5002")
def _url(path: str) -> str:
    return f"{STORAGE_BASE.rstrip('/')}/{path.lstrip('/')}"

BATCH_SIZE = int(os.getenv("SENTIMENT_BATCH_SIZE", "50"))

_sia = None

def _get_sia() -> SentimentIntensityAnalyzer:
    global _sia
    if _sia is None:
        try:
            _sia = SentimentIntensityAnalyzer()
        except LookupError:
            nltk.download("vader_lexicon")
            _sia = SentimentIntensityAnalyzer()
    return _sia

def quick_db_check():
    """Used by /ping to verify storage_service is reachable."""
    try:
        r = requests.get(_url("/posts/recent"), params={"limit": 1}, timeout=5)
        if not r.ok:
            return False, 0
        data = r.json()
        return True, (len(data) if isinstance(data, list) else 0)
    except Exception:
        return False, 0

def _bucket(compound: float) -> str:
    if compound >= 0.05:
        return "positive"
    if compound <= -0.05:
        return "negative"
    return "neutral"

def analyze_posts(limit: int = 20, subreddit: str | None = None):
    """Fetch posts from storage_service, analyze with VADER, POST results back."""
    limit = max(1, min(int(limit), 200))

    # 1) Fetch
    try:
        params = {"limit": limit}
        if subreddit:
            params["subreddit"] = subreddit
        r = requests.get(_url("/posts/recent"), params=params, timeout=20)
        r.raise_for_status()
        posts = r.json() or []
    except Exception as e:
        return [], {
            "error": "failed_to_fetch_posts",
            "details": str(e),
            "subreddit_filter": subreddit,
            "returned": 0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    # 2) Analyze
    sia = _get_sia()
    results = []
    for p in posts:
        title = (p.get("title") or "").strip()
        if not title:
            continue
        scores = sia.polarity_scores(title)
        comp = float(scores["compound"])
        results.append({
            "post_id": p.get("post_id"),
            "polarity": _bucket(comp),
            "compound": comp,
            "pos": float(scores["pos"]),
            "neu": float(scores["neu"]),
            "neg": float(scores["neg"]),
        })

    # 3) Store back
    store = None
    try:
        rr = requests.post(_url("/store-sentiment"),
                           json={"results": results}, timeout=20)
        rr.raise_for_status()
        store = rr.json()
    except Exception as e:
        store = {"error": "failed_to_store_sentiment", "details": str(e)}

    return results, {
        "subreddit_filter": subreddit,
        "fetched": len(posts),
        "analyzed": len(results),
        "store_result": store,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
