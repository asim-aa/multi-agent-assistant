from datetime import datetime
from zoneinfo import ZoneInfo

CITY_TIMEZONES = {
    # Asia — Japan
    "japan": "Asia/Tokyo",
    "tokyo": "Asia/Tokyo",
    "tokyo japan": "Asia/Tokyo",
    "tokyo, japan": "Asia/Tokyo",

    # Asia — India
    "india": "Asia/Kolkata",

    "bangalore": "Asia/Kolkata",
    "bangalore india": "Asia/Kolkata",
    "bangalore, india": "Asia/Kolkata",
    "bangalore karnataka india": "Asia/Kolkata",
    "bangalore, karnataka, india": "Asia/Kolkata",

    "bengaluru": "Asia/Kolkata",
    "bengaluru india": "Asia/Kolkata",
    "bengaluru, india": "Asia/Kolkata",
    "bengaluru karnataka india": "Asia/Kolkata",
    "bengaluru, karnataka, india": "Asia/Kolkata",

    # Asia — Middle East
    "iraq": "Asia/Baghdad",
    "baghdad": "Asia/Baghdad",
    "baghdad iraq": "Asia/Baghdad",
    "baghdad, iraq": "Asia/Baghdad",

    "dubai": "Asia/Dubai",
    "dubai uae": "Asia/Dubai",
    "dubai, uae": "Asia/Dubai",
    "dubai united arab emirates": "Asia/Dubai",
    "dubai, united arab emirates": "Asia/Dubai",

    "riyadh": "Asia/Riyadh",
    "riyadh saudi arabia": "Asia/Riyadh",
    "riyadh, saudi arabia": "Asia/Riyadh",

    # Europe
    "dublin": "Europe/Dublin",
    "dublin ireland": "Europe/Dublin",
    "dublin, ireland": "Europe/Dublin",

    "london": "Europe/London",
    "london uk": "Europe/London",
    "london, uk": "Europe/London",
    "london united kingdom": "Europe/London",
    "london, united kingdom": "Europe/London",

    "paris": "Europe/Paris",
    "paris france": "Europe/Paris",
    "paris, france": "Europe/Paris",

    "berlin": "Europe/Berlin",
    "berlin germany": "Europe/Berlin",
    "berlin, germany": "Europe/Berlin",

    # North America — United States
    "new york": "America/New_York",
    "new york usa": "America/New_York",
    "new york, usa": "America/New_York",
    "new york united states": "America/New_York",
    "new york, united states": "America/New_York",

    "los angeles": "America/Los_Angeles",
    "los angeles usa": "America/Los_Angeles",
    "los angeles, usa": "America/Los_Angeles",
    "los angeles united states": "America/Los_Angeles",
    "los angeles, united states": "America/Los_Angeles",

    "san francisco": "America/Los_Angeles",
    "san francisco usa": "America/Los_Angeles",
    "san francisco, usa": "America/Los_Angeles",
    "san francisco united states": "America/Los_Angeles",
    "san francisco, united states": "America/Los_Angeles",
}


def get_current_time(location: str) -> dict:
    location = location.strip()

    if not location:
        return {"error": "Location is required."}

    cleaned_location = normalize_location(location)
    timezone_name = CITY_TIMEZONES.get(cleaned_location)

    if not timezone_name:
        return {
            "error": (
                f"Time zone not found for '{location}'. "
                "Add this location to CITY_TIMEZONES in time_tools.py."
            )
        }

    now = datetime.now(ZoneInfo(timezone_name))

    return {
        "searched_for": location,
        "matched_location": cleaned_location,
        "timezone": timezone_name,
        "current_time": now.strftime("%I:%M %p"),
        "current_time_24h": now.strftime("%H:%M"),
        "date": now.strftime("%Y-%m-%d"),
        "weekday": now.strftime("%A"),
        "utc_offset": now.strftime("%z"),
    }


def normalize_location(location: str) -> str:
    cleaned = location.strip().lower()
    cleaned = cleaned.replace("?", "").replace(".", "").replace("!", "")

    if "time in " in cleaned:
        cleaned = cleaned.split("time in ", 1)[1]

    if "current time in " in cleaned:
        cleaned = cleaned.split("current time in ", 1)[1]

    if "what time is it in " in cleaned:
        cleaned = cleaned.split("what time is it in ", 1)[1]

    return cleaned.strip()