# app/routes/auth.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.database import get_db
from app.auth.password import hash_password, verify_password
from app.auth.jwt import create_token
from bson import ObjectId
from fastapi import Depends
router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email:    EmailStr
    password: str
    name:     str


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


# ── POST /auth/register ───────────────────────────────
@router.post("/register", status_code=201)
async def register(payload: RegisterRequest):
    db = get_db()

    # check duplicate email
    existing = await db.users.find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    # never store plain password
    # print("Password length:", len(payload.password))
    user = {
        "_id":       str(ObjectId()),
        "email":     payload.email,
        "name":      payload.name,
        "password":  hash_password(payload.password),
        "role":      "user",        # default role
        "is_banned": False,
    }

    await db.users.insert_one(user)

    # don't return password in response — ever
    return {
        "message": "account created. welcome to the gang.",
        "user_id": user["_id"],
        "email":   user["email"],
        "role":    user["role"]
    }


# ── POST /auth/login ──────────────────────────────────
@router.post("/login")
async def login(payload: LoginRequest):
    db = get_db()

    user = await db.users.find_one({"email": payload.email})

    # same error for wrong email OR wrong password
    # never reveal which one — security best practice
    if not user or not verify_password(payload.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.get("is_banned"):
        raise HTTPException(status_code=403, detail="Your account has been banned")

    token = create_token(user_id=user["_id"], role=user["role"])

    return {
        "access_token": token,
        "token_type":   "bearer",
        "role":         user["role"],
        "name":         user["name"]
    }


# ── GET /auth/me ──────────────────────────────────────
from fastapi import Depends
from app.auth.dependencies import get_current_user

@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    return {
        "id": user["_id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
    }