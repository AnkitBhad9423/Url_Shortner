# app/routes/analytics.py

from fastapi import APIRouter, HTTPException, Depends
from app.database import get_db
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api", tags=["analytics"])


# ── GET /api/analytics/{short_code} ───────────────────
@router.get("/analytics/{short_code}")
async def get_analytics(
    short_code: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()

    url_doc = await db.urls.find_one({"short_code": short_code})
    if not url_doc:
        raise HTTPException(status_code=404, detail="Short code not found")

    # ownership check
    if url_doc.get("user_id") != current_user["_id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="You can only view analytics for your own links")

    clicks = await db.clicks.find(
        {"short_code": short_code},
        {"_id": 0}
    ).to_list(length=1000)

    total    = len(clicks)
    countries = {}
    devices   = {}
    browsers  = {}

    for c in clicks:
        countries[c.get("country", "Unknown")] = countries.get(c.get("country", "Unknown"), 0) + 1
        devices[c.get("device",   "Unknown")]  = devices.get(c.get("device",   "Unknown"), 0) + 1
        browsers[c.get("browser", "Unknown")]  = browsers.get(c.get("browser", "Unknown"), 0) + 1

    def sorted_desc(d):
        return dict(sorted(d.items(), key=lambda x: x[1], reverse=True))

    return {
        "short_code":    short_code,
        "long_url":      url_doc["long_url"],
        "total_clicks":  total,
        "by_country":    sorted_desc(countries),
        "by_device":     sorted_desc(devices),
        "by_browser":    sorted_desc(browsers),
        "recent_clicks": clicks[-10:][::-1]
    }


# ── GET /api/analytics/{short_code}/timeline ──────────
@router.get("/analytics/{short_code}/timeline")
async def get_click_timeline(
    short_code: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()

    url_doc = await db.urls.find_one({"short_code": short_code})
    if not url_doc:
        raise HTTPException(status_code=404, detail="Short code not found")

    if url_doc.get("user_id") != current_user["_id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not your link")

    clicks = await db.clicks.find(
        {"short_code": short_code},
        {"_id": 0, "timestamp": 1}
    ).to_list(length=5000)

    timeline = {}
    for c in clicks:
        ts   = c.get("timestamp", "")
        date = ts[:10] if ts else "Unknown"
        timeline[date] = timeline.get(date, 0) + 1

    return {
        "short_code": short_code,
        "timeline":   dict(sorted(timeline.items()))
    }


# ── DELETE /api/analytics/{short_code} ────────────────
@router.delete("/analytics/{short_code}")
async def delete_analytics(
    short_code: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()

    doc = await db.urls.find_one({"short_code": short_code})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Short code '{short_code}' not found")

    # ownership check
    if doc.get("user_id") != current_user["_id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not your link")

    result = await db.clicks.delete_many({"short_code": short_code})

    return {
        "message":       f"analytics for '{short_code}' wiped. fresh start no cap.",
        "clicks_deleted": result.deleted_count
    }