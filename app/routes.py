# app/routes.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from app.schemas import ShortenRequest, ShortenResponse
from app.database import get_db, get_redis
from app.utils import encode_base62
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

router = APIRouter()


# ── POST /api/shorten ─────────────────────────────────────────────────────────
@router.post("/api/shorten", response_model=ShortenResponse)
async def shorten_url(payload: ShortenRequest):
    db = get_db()
    long_url = str(payload.long_url)

    # 1. Check if this URL was already shortened (avoid duplicates)
    existing = await db.urls.find_one({"long_url": long_url})
    if existing:
        short_code = existing["short_code"]
        return ShortenResponse(
            short_code=short_code,
            short_url=f"{BASE_URL}/{short_code}",
            long_url=long_url
        )

    # 2. Generate a unique short code using an atomic counter
    #    We keep a separate 'counters' collection with a single doc
    counter = await db.counters.find_one_and_update(
        {"_id": "url_counter"},
        {"$inc": {"seq": 1}},       # atomic increment — no race condition
        upsert=True,                # create if doesn't exist
        return_document=True
    )
    short_code = encode_base62(counter["seq"])

    # 3. Save to MongoDB
    await db.urls.insert_one({
        "short_code": short_code,
        "long_url":   long_url,
    })

    return ShortenResponse(
        short_code=short_code,
        short_url=f"{BASE_URL}/{short_code}",
        long_url=long_url
    )


# ── GET /{short_code} ─────────────────────────────────────────────────────────
@router.get("/{short_code}")
async def redirect_url(short_code: str):
    db    = get_db()
    redis = get_redis()

    # 1. Check Redis cache first
    cached = await redis.get(f"url:{short_code}")
    if cached:
        print(f"⚡ Cache HIT for {short_code}")
        return RedirectResponse(url=cached, status_code=302)

    # 2. Fall back to MongoDB
    doc = await db.urls.find_one({"short_code": short_code})
    if not doc:
        raise HTTPException(status_code=404, detail="Short URL not found")

    long_url = doc["long_url"]

    # 3. Store in Redis for next time (cache for 1 hour)
    await redis.set(f"url:{short_code}", long_url, ex=3600)
    print(f"💾 Cache MISS for {short_code} — saved to Redis")

    return RedirectResponse(url=long_url, status_code=302)