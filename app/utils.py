# app/utils.py

from urllib.parse import urlparse
import re
import httpx
import secrets
import string

BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def generate_random_code(length: int = 6) -> str:
    """Generate a cryptographically random Base62 string."""
    return ''.join(secrets.choice(BASE62) for _ in range(length))


BLACKLISTED_DOMAINS = {
    "malware.com",
    "phishing-site.com",
    "spam-domain.net",
    # add more as needed
}

# ── Reserved slugs that conflict with app routes ──────
RESERVED_SLUGS = {
    "health", "docs", "api", "admin", "login",
    "register", "static", "favicon.ico", "openapi.json"
}

def validate_url(url: str) -> tuple[bool, str]:
    """
    Returns (is_valid, error_message)
    """

    # 1. Length check
    if len(url) > 2048:
        return False, "URL exceeds maximum length of 2048 characters"

    # 2. Parse and check structure
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format"

    # 3. Must have proper scheme
    if parsed.scheme not in ("http", "https"):
        return False, "URL must start with http:// or https://"

    # 4. Must have a domain
    if not parsed.netloc:
        return False, "URL must have a valid domain"

    # 5. Basic domain format check
    domain = parsed.netloc.lower()
    # strip port if present
    domain = domain.split(":")[0]

    if not re.match(r"^[a-z0-9\-\.]+\.[a-z]{2,}$", domain):
        return False, "URL has an invalid domain format"

    # 6. Blacklist check
    # check exact domain and parent domain
    domain_parts = domain.split(".")
    for i in range(len(domain_parts) - 1):
        check = ".".join(domain_parts[i:])
        if check in BLACKLISTED_DOMAINS:
            return False, f"Domain '{domain}' is blacklisted"

    return True, ""


def is_reserved_slug(slug: str) -> bool:
    return slug.lower() in RESERVED_SLUGS



async def get_geo(ip: str) -> tuple[str, str]:
    """
    Returns (country, city) from IP.
    Uses ip-api.com — free, no API key, 45 req/min limit.
    Falls back to ("Unknown", "Unknown") on any error.
    """
    # skip geo for localhost/private IPs
    if ip in ("127.0.0.1", "localhost") or ip.startswith("192.168") or ip.startswith("10."):
        return "Local", "Local"

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"http://ip-api.com/json/{ip}?fields=country,city,status")
            data = resp.json()
            if data.get("status") == "success":
                return data.get("country", "Unknown"), data.get("city", "Unknown")
    except Exception:
        pass

    return "Unknown", "Unknown"


async def is_ip_blacklisted(ip: str, redis) -> bool:
    """
    Check if IP is in Redis blacklist.
    Key format: blacklist:ip:{ip}
    """
    try:
        result = await redis.get(f"blacklist:ip:{ip}")
        return result is not None
    except Exception:
        return False


async def blacklist_ip(ip: str, redis, reason: str = "", ttl_seconds: int = 86400):
    """
    Add IP to Redis blacklist.
    Default TTL: 24 hours.
    """
    try:
        await redis.set(
            f"blacklist:ip:{ip}",
            reason or "blacklisted",
            ex=ttl_seconds
        )
    except Exception:
        pass