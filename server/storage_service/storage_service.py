# storage_service.py
from datetime import datetime
from typing import Any, Optional

from mongoengine import (
    Document,
    StringField,
    IntField,
    BooleanField,
    DateTimeField,
    FloatField,
)

 # ensures Mongo connection is established

class Post(Document):
    # Core Reddit fields
    post_id = StringField(required=True, unique=True)
    title = StringField()
    author = StringField()
    subreddit = StringField()
    score = IntField()
    num_comments = IntField()
    created_utc = DateTimeField()
    url = StringField()
    is_video = BooleanField()

    # Sentiment fields (set by sentiment_service)
    sentiment_polarity = StringField()   # "positive" | "neutral" | "negative"
    sentiment_compound = FloatField()    # VADER compound (-1..1)
    sentiment_pos = FloatField()
    sentiment_neu = FloatField()
    sentiment_neg = FloatField()

    meta = {
        "indexes": [
            "post_id",
            "-created_utc",
            "subreddit",
            "sentiment_polarity",
        ]
    }


def _extract_flat_posts(payload: Any) -> list[dict]:
    """
    Normalize inputs to a flat list of Reddit post dicts.
    Accepts:
      - Full Reddit Listing: {"kind":"Listing","data":{"children":[{"data":{...}}, ...]}}
      - {"data":{"children":[...]}}, or {"children":[...]}
      - Already-flat: [{"id":...}, ...]
      - Nested: {"top":{"python": {"data":{"children":[...]}}}}, etc.
    """
    items: list[dict] = []

    def handle_listing(listing: dict):
        children = ((listing.get("data") or {}).get("children")) or []
        for child in children:
            d = (child or {}).get("data") or {}
            if isinstance(d, dict) and d:
                items.append(d)

    def walk(obj: Any):
        if isinstance(obj, dict):
            d = obj.get("data")
            if isinstance(d, dict) and isinstance(d.get("children"), list):
                handle_listing(obj)
                return
            if isinstance(obj.get("children"), list):
                handle_listing({"data": obj})
                return
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                if isinstance(v, dict) and "data" in v and isinstance(v["data"], dict):
                    items.append(v["data"])
                else:
                    walk(v)

    walk(payload)

    seen = set()
    out: list[dict] = []
    for d in items:
        key = d.get("id") or d.get("name") or id(d)
        if key in seen:
            continue
        seen.add(key)
        out.append(d)
    return out


def _to_datetime(ts: Any) -> Optional[datetime]:
    if ts is None:
        return None
    try:
        return datetime.utcfromtimestamp(int(float(ts)))
    except Exception:
        return None


def upsert_posts(payload: dict) -> int:
    """Insert/update Reddit posts coming from reddit_service."""
    flat = _extract_flat_posts(payload)
    count = 0
    for d in flat:
        pid = d.get("id") or d.get("name")  # e.g. "abc123" or "t3_abc123"
        if not pid:
            continue

        created_dt = _to_datetime(d.get("created_utc") or d.get("created"))

        Post.objects(post_id=pid).update_one(
            set__post_id=pid,
            set__title=d.get("title"),
            set__author=d.get("author"),
            set__subreddit=d.get("subreddit"),
            set__score=d.get("score"),
            set__num_comments=d.get("num_comments"),
            set__created_utc=created_dt,
            set__url=d.get("url"),
            set__is_video=d.get("is_video"),
            upsert=True,
        )
        count += 1

    return count


def upsert_sentiment(results: list[dict]) -> int:
    """
    Update sentiment fields for existing posts.
    Expected item shape:
      {
        "post_id": "...",
        "polarity": "positive"|"neutral"|"negative",
        "compound": 0.123,
        "pos": 0.1, "neu": 0.7, "neg": 0.2
      }
    """
    if not isinstance(results, list):
        raise ValueError("results must be a list")

    updated = 0
    for r in results:
        pid = (r or {}).get("post_id")
        if not pid:
            continue

        q = Post.objects(post_id=pid)
        if not q:
            # Skip creating new docs from sentiment only
            continue

        q.update_one(
            set__sentiment_polarity=r.get("polarity"),
            set__sentiment_compound=r.get("compound"),
            set__sentiment_pos=r.get("pos"),
            set__sentiment_neu=r.get("neu"),
            set__sentiment_neg=r.get("neg"),
            upsert=False,
        )
        updated += 1

    return updated


def get_recent_posts(limit: int = 20, subreddit: Optional[str] = None) -> list[dict]:
    limit = max(1, min(int(limit), 200))
    q = Post.objects
    if subreddit:
        q = q.filter(subreddit__iexact=subreddit)

    posts = q.order_by("-created_utc")[:limit]
    data: list[dict] = []
    for p in posts:
        row = {
            "post_id": p.post_id,
            "title": p.title,
            "author": p.author,
            "subreddit": p.subreddit,
            "score": p.score,
            "num_comments": p.num_comments,
            "created_utc": p.created_utc.isoformat() if p.created_utc else None,
            "url": p.url,
            "is_video": p.is_video,
        }
        # include sentiment only if present
        if p.sentiment_compound is not None:
            row["sentiment"] = {
                "polarity": p.sentiment_polarity,
                "compound": p.sentiment_compound,
                "pos": p.sentiment_pos,
                "neu": p.sentiment_neu,
                "neg": p.sentiment_neg,
            }
        data.append(row)
    return data

def store_sentiment_results(results: list[dict]) -> int:
    """Alias for backward/alternate import style."""
    return upsert_sentiment(results)

def apply_sentiment_batch(analyses: list[dict]) -> int:
    """Alias used by an older route name."""
    return upsert_sentiment(analyses)