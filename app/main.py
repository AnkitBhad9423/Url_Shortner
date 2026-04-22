# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import connect_mongo, close_mongo, connect_redis, close_redis
from app.routes import router


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
    version="1.0.0",
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # for dev/learning — lock this down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




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