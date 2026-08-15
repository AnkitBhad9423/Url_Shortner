# app/routes/links.py

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
from app.schemas import ShortenRequest, ShortenResponse
from app.database import get_db, get_redis
from app.utils import generate_random_code, validate_url, is_reserved_slug, get_geo, is_ip_blacklisted
from app.models import create_click_doc
from app.auth.dependencies import get_current_user, get_admin_user
from dotenv import load_dotenv
import os

load_dotenv()
BASE_URL = os.getenv("FRONTEND_URL", "http://localhost:8000")

router = APIRouter(tags=["links"])


# ── POST /api/shorten ─────────────────────────────────
@router.post("/api/shorten", response_model=ShortenResponse)
async def shorten_url(
    payload: ShortenRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)   # ← auth added
):
    db    = get_db()
    redis = get_redis()
    long_url = str(payload.long_url)
    ip = request.client.host

    # 1. Validate URL
    is_valid, error = validate_url(long_url)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # 2. IP blacklist check
    if await is_ip_blacklisted(ip, redis):
        raise HTTPException(status_code=403, detail="Your IP is blacklisted")

    # 3. Duplicate check — scoped to this user
    try:
        existing = await db.urls.find_one({
            "long_url": long_url,
            "user_id":  current_user["_id"]    # ← each user gets their own short code
        })
        if existing:
            short_code = existing["short_code"]
            return ShortenResponse(
                short_code=short_code,
                short_url=f"{BASE_URL}/ch/{short_code}",
                long_url=long_url
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # 4. Generate unique random short code — your existing logic, unchanged
    MAX_RETRIES = 5
    for attempt in range(MAX_RETRIES):
        short_code = generate_random_code(6)

        if is_reserved_slug(short_code):
            short_code = f"_{short_code}"

        try:
            existing_code = await db.urls.find_one({"short_code": short_code})
            if not existing_code:
                await db.urls.insert_one({
                    "short_code":    short_code,
                    "long_url":      long_url,
                    "created_by_ip": ip,
                    "user_id":       current_user["_id"],    # ← ownership
                    "created_by":    current_user["email"],
                })
                return ShortenResponse(
                    short_code=short_code,
                    short_url=f"{BASE_URL}/ch/{short_code}",  # ← kept /ch/ prefix
                    long_url=long_url
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Insert error: {str(e)}")

    raise HTTPException(status_code=500, detail="Failed to generate unique short code. try again.")


# ── GET /ch/{short_code} ──────────────────────────────
# redirect is PUBLIC — no auth needed, anyone with the link can use it
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


# ── GET /api/links — user sees only their own links ───
@router.get("/api/links")
async def get_my_links(current_user: dict = Depends(get_current_user)):
    print("Current user:", current_user)  # Debugging line
    db = get_db()

    links = await db.urls.find(
        {"user_id": current_user["_id"]},
        {"_id": 0}
    ).to_list(length=100)
    print("Retrieved links:", links)  # Debugging line
    for link in links:
        link["click_count"] = await db.clicks.count_documents(
            {"short_code": link["short_code"]}
        )

    return {"links": links, "total": len(links)}


# ── DELETE /api/links/all — admin only ────────────────
# IMPORTANT: this must be defined BEFORE /{short_code}
# otherwise FastAPI treats "all" as a short_code value
@router.delete("/api/links/all")
async def delete_all_links(admin: dict = Depends(get_admin_user)):
    db    = get_db()
    redis = get_redis()

    url_count   = await db.urls.count_documents({})
    click_count = await db.clicks.count_documents({})

    await db.urls.delete_many({})
    await db.clicks.delete_many({})

    # reset counter — your existing logic preserved
    await db.counters.update_one(
        {"_id": "url_counter"},
        {"$set": {"seq": 0}}
    )

    try:
        keys = await redis.keys("url:*")
        if keys:
            await redis.delete(*keys)
    except Exception as e:
        print(f"⚠️ Redis flush failed: {e}")

    return {
        "message":      "everything's gone bestie. clean slate era.",
        "urls_deleted":  url_count,
        "clicks_deleted": click_count
    }


# ── DELETE /api/links/{short_code} ────────────────────
@router.delete("/api/links/{short_code}")
async def delete_link(
    short_code: str,
    current_user: dict = Depends(get_current_user)
):
    db    = get_db()
    redis = get_redis()

    doc = await db.urls.find_one({"short_code": short_code})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Short code '{short_code}' not found")

    # ownership check — user can only delete their own, admin can delete any
    if doc.get("user_id") != current_user["_id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not your link bestie")

    await db.urls.delete_one({"short_code": short_code})
    await db.clicks.delete_many({"short_code": short_code})

    try:
        await redis.delete(f"url:{short_code}")
    except Exception as e:
        print(f"⚠️ Redis delete failed: {e}")

    return {
        "message": f"short code '{short_code}' has been deleted. it's dead fr.",
        "deleted":  short_code
    }