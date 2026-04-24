# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import connect_mongo, close_mongo, connect_redis, close_redis
from app.middleware import IPBlacklistMiddleware, SlidingWindowRateLimiter
from app.routes import router
from fastapi.responses import FileResponse
import os
from pathlib import Path
# ── Lifespan (replaces @app.on_event which is now deprecated) ────────────────
# This runs ONCE when the app starts and ONCE when it shuts down
# Think of it like Django's AppConfig.ready() but for async connections

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await connect_mongo()
    await connect_redis()
    yield                   # app runs here
    # shutdown
    await close_mongo()
    await close_redis()


app = FastAPI(
    title="URL Shortener",
    description="A simple URL shortener built with FastAPI + MongoDB + Redis",
    version="2.0.0",
    lifespan=lifespan
)
app.add_middleware(CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SlidingWindowRateLimiter,
    requests_per_window=20,
    window_seconds=60
)
app.add_middleware(IPBlacklistMiddleware)

@app.get("/")
async def serve_frontend():
    BASE_DIR = Path(__file__).resolve().parent.parent
    file_path = BASE_DIR / "templates" / "index.html"
    return FileResponse(file_path)

@app.get("/health")
async def health():
    from app.database import get_db, get_redis
    status = {"app": "ok", "mongodb": "unknown", "redis": "unknown"}
    try:
        db = get_db()
        if db is None:
            status["mongodb"] = "❌ not connected"
        else:
            await db.client.admin.command("ping")
            status["mongodb"] = "✅ connected"
    except Exception as e:
        status["mongodb"] = f"❌ {str(e)}"
    try:
        redis = get_redis()
        if redis is None:
            status["redis"] = "❌ not connected"
        else:
            await redis.ping()
            status["redis"] = "✅ connected"
    except Exception as e:
        status["redis"] = f"❌ {str(e)}"
    return status



app.include_router(router)