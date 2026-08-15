# app/auth/jwt.py
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
import os

SECRET_KEY      = os.getenv("SECRET_KEY_JWT")
ALGORITHM       = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24   # 24 hours


def create_token(user_id: str, role: str) -> str:
    """
    Create a signed JWT token.
    Payload contains user identity + role + expiry.
    """
    payload = {
        "sub":  user_id,          # subject — who this token belongs to
        "role": role,             # "user" or "admin"
        "exp":  datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Verify token signature + expiry.
    Returns payload if valid, raises 401 if not.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")