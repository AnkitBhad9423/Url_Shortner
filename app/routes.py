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
# app/routes.py  — POST /api/shorten

@router.post("/api/shorten", response_model=ShortenResponse)
async def shorten_url(payload: ShortenRequest):
    db = get_db()
    long_url = str(payload.long_url)

    # 1. Check duplicate
    try:
        existing = await db.urls.find_one({"long_url": long_url})
        if existing:
            short_code = existing["short_code"]
            return ShortenResponse(
                short_code=short_code,
                short_url=f"{BASE_URL}/{short_code}",
                long_url=long_url
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # 2. Atomic counter
    try:
        counter = await db.counters.find_one_and_update(
            {"_id": "url_counter"},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Counter error: {str(e)}")

    short_code = encode_base62(counter["seq"])

    # 3. Save to MongoDB
    try:
        await db.urls.insert_one({
            "short_code": short_code,
            "long_url":   long_url,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insert error: {str(e)}")

    return ShortenResponse(
        short_code=short_code,
        short_url=f"{BASE_URL}/{short_code}",
        long_url=long_url
    )

# ── GET /{short_code} ─────────────────────────────────────────────────────────
# app/routes.py

@router.get("/{short_code}")
async def redirect_url(short_code: str):
    db    = get_db()
    redis = get_redis()

    # 1. Check Redis cache first — but don't crash if Redis fails
    try:
        cached = await redis.get(f"url:{short_code}")
        if cached:
            print(f"⚡ Cache HIT for {short_code}")
            return RedirectResponse(url=cached, status_code=302)
    except Exception as e:
        print(f"⚠️ Redis error (falling back to MongoDB): {e}")

    # 2. Fall back to MongoDB
    try:
        doc = await db.urls.find_one({"short_code": short_code})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if not doc:
        raise HTTPException(status_code=404, detail="Short URL not found")

    long_url = doc["long_url"]

    # 3. Try to cache in Redis — but don't crash if it fails
    try:
        await redis.set(f"url:{short_code}", long_url, ex=3600)
        print(f"💾 Cached {short_code} in Redis")
    except Exception as e:
        print(f"⚠️ Redis set failed (continuing anyway): {e}")

    return RedirectResponse(url=long_url, status_code=302)