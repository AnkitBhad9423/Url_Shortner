# app/database.py

from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
from dotenv import load_dotenv
import os

load_dotenv()

# ── MongoDB ───────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME   = os.getenv("DB_NAME", "urlshortener")

# These are module-level variables, set during app startup
mongo_client: AsyncIOMotorClient = None
db = None

async def connect_mongo():
    global mongo_client, db
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    db = mongo_client[DB_NAME]
    print("✅ MongoDB connected")

async def close_mongo():
    mongo_client.close()
    print("🔴 MongoDB disconnected")

def get_db():
    return db   # called in routes to get the db reference


# ── Redis ─────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

redis_client: Redis = None

async def connect_redis():
    global redis_client
    try:
        # import ssl
        # ssl_context = ssl.create_default_context()
        # ssl_context.check_hostname = False
        # ssl_context.verify_mode = ssl.CERT_NONE

        redis_client = Redis.from_url(
            REDIS_URL,
            decode_responses=True
        )
        await redis_client.ping()
        print("✅ Redis connected")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")

async def close_redis():
    await redis_client.aclose()
    print("🔴 Redis disconnected")

def get_redis():
    return redis_client  # called in routes to get the redis reference