# app/routes.py

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from app.schemas import ShortenRequest, ShortenResponse
from app.database import get_db, get_redis
from app.utils import generate_random_code, validate_url, is_reserved_slug, get_geo, is_ip_blacklisted
from app.models import create_click_doc
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

router = APIRouter()


# ── POST /api/shorten ─────────────────────────────────────────────────────────
# app/routes.py  — POST /api/shorten

@router.post("/api/shorten", response_model=ShortenResponse)
async def shorten_url(payload: ShortenRequest, request: Request):
    db    = get_db()
    redis = get_redis()
    long_url = str(payload.long_url)
    ip = request.client.host

    # 1. Validate URL
    is_valid, error = validate_url(long_url)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # 2. Check IP blacklist
    if await is_ip_blacklisted(ip, redis):
        raise HTTPException(status_code=403, detail="Your IP is blacklisted")

    # 3. Duplicate check (optional – same long URL returns existing short code)
    try:
        existing = await db.urls.find_one({"long_url": long_url})
        if existing:
            short_code = existing["short_code"]
            return ShortenResponse(
                short_code=short_code,
                short_url=f"{BASE_URL}/jstlernnganks/{short_code}",
                long_url=long_url
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # 4. Generate a unique random short code (with retries)
    MAX_RETRIES = 5
    for attempt in range(MAX_RETRIES):
        short_code = generate_random_code(6)   # adjust length as needed
        
        # Handle reserved slugs
        if is_reserved_slug(short_code):
            short_code = f"_{short_code}"
        
        # Check if code already exists in DB
        try:
            existing_code = await db.urls.find_one({"short_code": short_code})
            if not existing_code:
                # Save to MongoDB
                await db.urls.insert_one({
                    "short_code": short_code,
                    "long_url":   long_url,
                    "created_by_ip": ip,
                })
                return ShortenResponse(
                    short_code=short_code,
                    short_url=f"{BASE_URL}/jstlernnganks/{short_code}",
                    long_url=long_url
                )
            # else collision – continue loop
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Insert error: {str(e)}")
    
    # If we exhaust retries (extremely unlikely with 6‑char random)
    raise HTTPException(status_code=500, detail="Failed to generate unique short code")
# ── GET /{short_code} ─────────────────────────────────────────────────────────
# app/routes.py

@router.get("/ch/{short_code}")
async def redirect_url(short_code: str, request: Request):
    db    = get_db()
    redis = get_redis()
    ip    = request.client.host
    ua    = request.headers.get("user-agent", "")

    # 1. Redis cache check
    try:
        cached = await redis.get(f"url:{short_code}")
        if cached:
            print(f"⚡ Cache HIT for {short_code}")
            # track click async-style (don't await geo to keep redirect fast)
            country, city = await get_geo(ip)
            click = create_click_doc(short_code, ip, ua, country, city)
            await db.clicks.insert_one(click)
            return RedirectResponse(url=cached, status_code=302)
    except Exception as e:
        print(f"⚠️ Redis error: {e}")

    # 2. MongoDB lookup
    try:
        doc = await db.urls.find_one({"short_code": short_code})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if not doc:
        raise HTTPException(status_code=404, detail="Short URL not found")

    long_url = doc["long_url"]

    # 3. Cache in Redis
    try:
        await redis.set(f"url:{short_code}", long_url, ex=3600)
    except Exception as e:
        print(f"⚠️ Redis set failed: {e}")

    # 4. Track click
    try:
        country, city = await get_geo(ip)
        click = create_click_doc(short_code, ip, ua, country, city)
        await db.clicks.insert_one(click)
    except Exception as e:
        print(f"⚠️ Click tracking failed: {e}")

    return RedirectResponse(url=long_url, status_code=302)


# ── GET /api/analytics/{short_code} ───────────────────
@router.get("/api/analytics/{short_code}")
async def get_analytics(short_code: str):
    db = get_db()

    # verify short code exists
    url_doc = await db.urls.find_one({"short_code": short_code})
    if not url_doc:
        raise HTTPException(status_code=404, detail="Short code not found")

    # aggregate click data
    clicks = await db.clicks.find(
        {"short_code": short_code},
        {"_id": 0}   # exclude MongoDB _id from results
    ).to_list(length=1000)

    # simple aggregations
    total   = len(clicks)
    countries = {}
    devices   = {}
    browsers  = {}

    for c in clicks:
        countries[c.get("country", "Unknown")] = countries.get(c.get("country", "Unknown"), 0) + 1
        devices[c.get("device", "Unknown")]     = devices.get(c.get("device", "Unknown"), 0) + 1
        browsers[c.get("browser", "Unknown")]   = browsers.get(c.get("browser", "Unknown"), 0) + 1

    return {
        "short_code":  short_code,
        "long_url":    url_doc["long_url"],
        "total_clicks": total,
        "by_country":  countries,
        "by_device":   devices,
        "by_browser":  browsers,
        "recent_clicks": clicks[-10:]  # last 10 clicks
    }

# ── DELETE /api/links/{short_code} ────────────────────────────────────────────
@router.delete("/api/links/{short_code}")
async def delete_link(short_code: str):
    db    = get_db()
    redis = get_redis()

    # check if exists first
    doc = await db.urls.find_one({"short_code": short_code})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Short code '{short_code}' not found")

    # delete from MongoDB — urls collection
    await db.urls.delete_one({"short_code": short_code})

    # delete all click analytics for this link
    await db.clicks.delete_many({"short_code": short_code})

    # invalidate Redis cache
    try:
        await redis.delete(f"url:{short_code}")
    except Exception as e:
        print(f"⚠️ Redis delete failed: {e}")

    return {
        "message": f"short code '{short_code}' has been deleted. it's dead fr.",
        "deleted": short_code
    }


# ── DELETE /api/links/all ──────────────────────────────────────────────────────
@router.delete("/api/links/all")
async def delete_all_links():
    db    = get_db()
    redis = get_redis()

    # count before deleting so we can report back
    url_count   = await db.urls.count_documents({})
    click_count = await db.clicks.count_documents({})

    # wipe both collections
    await db.urls.delete_many({})
    await db.clicks.delete_many({})

    # reset the counter so short codes start from 1 again
    await db.counters.update_one(
        {"_id": "url_counter"},
        {"$set": {"seq": 0}}
    )

    # flush all URL cache keys from Redis
    try:
        keys = await redis.keys("url:*")
        if keys:
            await redis.delete(*keys)
    except Exception as e:
        print(f"⚠️ Redis flush failed: {e}")

    return {
        "message": "everything's gone bestie. clean slate era.",
        "urls_deleted":   url_count,
        "clicks_deleted": click_count
    }


# ── DELETE /api/analytics/{short_code} ───────────────────────────────────────
# delete only analytics, keep the link alive
@router.delete("/api/analytics/{short_code}")
async def delete_analytics(short_code: str):
    db = get_db()

    doc = await db.urls.find_one({"short_code": short_code})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Short code '{short_code}' not found")

    result = await db.clicks.delete_many({"short_code": short_code})

    return {
        "message": f"analytics for '{short_code}' wiped. fresh start no cap.",
        "clicks_deleted": result.deleted_count
    }
