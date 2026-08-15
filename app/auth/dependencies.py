# app/auth/dependencies.py
from fastapi import Depends, HTTPException, Header
from app.auth.jwt import decode_token
from app.database import get_db


async def get_current_user(authorization: str = Header(None)):

    print("========== AUTH START ==========")
    print("Authorization exists:", authorization is not None)

    # STEP 1
    if not authorization:
        print("❌ STEP 1 FAILED: No Authorization header")
        raise HTTPException(
            status_code=401,
            detail="DEBUG: Missing Authorization header"
        )

    print("Authorization:", authorization[:30] + "...")

    # STEP 2
    if not authorization.startswith("Bearer "):
        print("❌ STEP 2 FAILED: Invalid Bearer format")
        raise HTTPException(
            status_code=401,
            detail="DEBUG: Invalid Authorization format"
        )

    token = authorization[len("Bearer "):].strip()

    print("Token length:", len(token))

    # STEP 3
    try:
        payload = decode_token(token)
        print("✅ STEP 3 JWT DECODE SUCCESS")
        print("Payload:", payload)

    except Exception as e:
        print("❌ STEP 3 JWT DECODE FAILED")
        print("Exception:", repr(e))

        raise HTTPException(
            status_code=401,
            detail=f"DEBUG JWT ERROR: {str(e)}"
        )

    # STEP 4
    if "sub" not in payload:
        print("❌ STEP 4 FAILED: No sub in JWT")
        raise HTTPException(
            status_code=401,
            detail="DEBUG: JWT has no sub"
        )

    user_id = payload["sub"]

    print("User ID from token:", user_id)

    # STEP 5
    try:
        db = get_db()

        print("DB object exists:", db is not None)

        user = await db.users.find_one({
            "_id": user_id
        })

        print("User found:", user is not None)

    except Exception as e:
        print("❌ STEP 5 DATABASE ERROR")
        print("Exception:", repr(e))

        raise HTTPException(
            status_code=401,
            detail=f"DEBUG DB ERROR: {str(e)}"
        )

    # STEP 6
    if not user:
        print("❌ STEP 6 FAILED: User not found")
        raise HTTPException(
            status_code=401,
            detail=f"DEBUG: User not found for ID {user_id}"
        )

    print("✅ AUTH SUCCESS")
    print("User:", user)
    print("========== AUTH END ==========")

    return user


async def get_admin_user(current_user: dict = Depends(get_current_user)):
    """
    Extends get_current_user — additionally checks role is admin.
    Use this as Depends() on admin-only routes.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to do this"
        )
    return current_user