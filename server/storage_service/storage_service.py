# storage_service.py  (NO Flask app here)

from mongoengine import Document, StringField, IntField, BooleanField, DateTimeField
from datetime import datetime
import database  # ensures Mongo connection is established
from typing import Optional

# MongoEngine document
class Post(Document):
    post_id = StringField(required=True, unique=True)
    title = StringField()
    author = StringField()
    subreddit = StringField()
    score = IntField()
    num_comments = IntField()
    created_utc = DateTimeField()
    url = StringField()
    is_video = BooleanField()

def upsert_posts(payload: dict) -> int:
    """
    Insert/update posts coming from reddit_service.
    Returns number of posts processed.
    """
    if not payload:
        return 0

    count = 0
    for _, subreddits in payload.items():          # category -> subreddits
        for _, posts in subreddits.items():         # subreddit -> posts blob
            for post in posts.get("data", {}).get("children", []):
                post_data = post["data"]

                created_utc = post_data.get("created_utc")
                created_dt = datetime.utcfromtimestamp(created_utc) if created_utc else None

                Post.objects(post_id=post_data["id"]).update_one(
                    set__title=post_data.get("title"),
                    set__author=post_data.get("author"),
                    set__subreddit=post_data.get("subreddit"),
                    set__score=post_data.get("score"),
                    set__num_comments=post_data.get("num_comments"),
                    set__created_utc=created_dt,
                    set__url=post_data.get("url"),
                    set__is_video=post_data.get("is_video"),
                    upsert=True
                )
                count += 1
    return count

def get_recent_posts(limit: int = 20, subreddit: Optional[str] = None) -> list[dict]:
    """
    Read recent posts from MongoDB, optionally filtered by subreddit.
    Returns list of dicts.
    """
    limit = max(1, min(limit, 200))
    q = Post.objects
    if subreddit:
        q = q.filter(subreddit__iexact=subreddit)

    posts = q.order_by("-created_utc")[:limit]
    return [
        {
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
        for p in posts
    ]
