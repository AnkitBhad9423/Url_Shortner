# app/auth/dependencies.py
from fastapi import Depends, HTTPException, Header
from app.auth.jwt import decode_token
from app.database import get_db


async def get_current_user(authorization: str = Header(None)):
    """
    Extracts and validates JWT from Authorization header.
    Use this as Depends() on any route that needs a logged-in user.

    Client must send:  Authorization: Bearer <token>
    """
    print("Authorization header:", authorization)  # Debugging line
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header"
        )

    token = authorization.split(" ")[1]
    payload = decode_token(token)

    db = get_db()
    user = await db.users.find_one({"_id": payload["sub"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user   # this gets injected into your route function


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