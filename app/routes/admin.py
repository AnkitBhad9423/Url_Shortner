# app/routes/admin.py
from fastapi import APIRouter, HTTPException, Depends
from app.database import get_db, get_redis
from app.auth.dependencies import get_admin_user  # ← admin only

router = APIRouter(prefix="/admin", tags=["admin"])


# ── GET /admin/users — see all users ──────────────────
@router.get("/users")
async def get_all_users(admin: dict = Depends(get_admin_user)):
    db    = get_db()
    users = await db.users.find(
        {},
        {"password": 0}    # never return passwords
    ).to_list(length=500)

    for u in users:
        u["_id"] = str(u["_id"])
        u["link_count"] = await db.urls.count_documents({"user_id": str(u["_id"])})

    return {"users": users, "total": len(users)}


# ── POST /admin/users/{user_id}/ban ───────────────────
@router.post("/users/{user_id}/ban")
async def ban_user(user_id: str, admin: dict = Depends(get_admin_user)):
    db = get_db()

    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("role") == "admin":
        raise HTTPException(status_code=400, detail="Cannot ban an admin")

    await db.users.update_one(
        {"_id": user_id},
        {"$set": {"is_banned": True}}
    )

    return {"message": f"user {user_id} banned. they're cooked."}


# ── POST /admin/users/{user_id}/unban ─────────────────
@router.post("/users/{user_id}/unban")
async def unban_user(user_id: str, admin: dict = Depends(get_admin_user)):
    db = get_db()
    await db.users.update_one(
        {"_id": user_id},
        {"$set": {"is_banned": False}}
    )
    return {"message": f"user {user_id} unbanned. second chance arc."}


# ── GET /admin/links — see ALL links globally ─────────
@router.get("/links")
async def get_all_links(admin: dict = Depends(get_admin_user)):
    db    = get_db()
    links = await db.urls.find({}, {"_id": 0}).to_list(length=1000)

    for link in links:
        link["click_count"] = await db.clicks.count_documents(
            {"short_code": link["short_code"]}
        )

    return {"links": links, "total": len(links)}


# ── DELETE /admin/links/{code} — admin force delete ───
@router.delete("/links/{short_code}")
async def admin_delete_link(
    short_code: str,
    admin: dict = Depends(get_admin_user)
):
    db    = get_db()
    redis = get_redis()

    doc = await db.urls.find_one({"short_code": short_code})
    if not doc:
        raise HTTPException(status_code=404, detail="Link not found")

    await db.urls.delete_one({"short_code": short_code})
    await db.clicks.delete_many({"short_code": short_code})

    try:
        await redis.delete(f"url:{short_code}")
    except Exception:
        pass

    return {"message": f"admin deleted '{short_code}'. rip bozo."}


# ── GET /admin/stats — system wide analytics ──────────
@router.get("/stats")
async def get_system_stats(admin: dict = Depends(get_admin_user)):
    db = get_db()

    total_users  = await db.users.count_documents({})
    total_links  = await db.urls.count_documents({})
    total_clicks = await db.clicks.count_documents({})
    banned_users = await db.users.count_documents({"is_banned": True})

    return {
        "total_users":   total_users,
        "total_links":   total_links,
        "total_clicks":  total_clicks,
        "banned_users":  banned_users,
    }


# ── POST /admin/blacklist/domain ──────────────────────
@router.post("/blacklist/domain")
async def blacklist_domain(
    domain: str,
    admin: dict = Depends(get_admin_user)
):
    redis = get_redis()
    await redis.set(f"blacklist:domain:{domain}", "blocked")
    return {"message": f"domain '{domain}' blacklisted globally"}