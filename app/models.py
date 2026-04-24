# app/models.py

from datetime import datetime, timezone


def create_click_doc(
    short_code: str,
    ip: str,
    user_agent_str: str,
    country: str,
    city: str,
) -> dict:
    """
    Build the click tracking document to insert into MongoDB
    """
    # parse device + browser from user agent string
    from user_agents import parse
    ua = parse(user_agent_str or "")

    # detect device type
    if ua.is_mobile:
        device = "mobile"
    elif ua.is_tablet:
        device = "tablet"
    elif ua.is_pc:
        device = "desktop"
    else:
        device = "unknown"

    return {
        "short_code": short_code,
        "timestamp":  datetime.now(timezone.utc).isoformat(),
        "ip":         ip,
        "country":    country,
        "city":       city,
        "device":     device,
        "browser":    ua.browser.family,
        "os":         ua.os.family,
    }