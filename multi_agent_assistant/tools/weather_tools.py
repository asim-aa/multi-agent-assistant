import requests


US_STATE_ALIASES = {
    "ca": "california",
    "california": "california",
    "ny": "new york",
    "new york": "new york",
    "tx": "texas",
    "texas": "texas",
    "fl": "florida",
    "florida": "florida",
}


LOCATION_ALIASES = {
    "tokyo,japan": "Tokyo, Tokyo, Japan",
    "tokyo, japan": "Tokyo, Tokyo, Japan",
    "tokyo japan": "Tokyo, Tokyo, Japan",
    "dublin,ca": "Dublin, California, USA",
    "dublin, ca": "Dublin, California, USA",
    "dublin ca": "Dublin, California, USA",
    "dublin,california": "Dublin, California, USA",
    "dublin, california": "Dublin, California, USA",
}


COUNTRY_ALIASES = {
    "usa": "united states",
    "us": "united states",
    "united states of america": "united states",
    "japan": "japan",
    "ireland": "ireland",
}


def get_weather(location: str) -> dict:
    location = normalize_location_query(location)

    parts = [part.strip() for part in location.split(",")]

    city = parts[0] if len(parts) > 0 else location
    state_or_region = parts[1] if len(parts) > 1 else ""
    country = parts[2] if len(parts) > 2 else ""

    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo_params = {
        "name": city,
        "count": 25,
        "language": "en",
        "format": "json",
    }

    try:
        geo_response = requests.get(geo_url, params=geo_params, timeout=10)
        geo_response.raise_for_status()
    except requests.RequestException as error:
        return {"error": f"Geocoding API request failed: {error}"}

    geo_data = geo_response.json()
    results = geo_data.get("results", [])

    if not results:
        return {"error": f"Could not find city: {city}"}

    selected_place = choose_best_location(
        results=results,
        city=city,
        state_or_region=state_or_region,
        country=country,
    )

    if selected_place is None:
        available_matches = [
            {
                "name": place.get("name"),
                "state_or_region": place.get("admin1"),
                "country": place.get("country"),
                "country_code": place.get("country_code"),
            }
            for place in results[:10]
        ]

        return {
            "error": f"Could not confidently match location: {location}",
            "available_matches": available_matches,
        }

    latitude = selected_place["latitude"]
    longitude = selected_place["longitude"]

    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "apparent_temperature,"
            "precipitation,"
            "weather_code,"
            "wind_speed_10m"
        ),
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
    }

    try:
        weather_response = requests.get(weather_url, params=weather_params, timeout=10)
        weather_response.raise_for_status()
    except requests.RequestException as error:
        return {"error": f"Weather API request failed: {error}"}

    weather_data = weather_response.json()

    return {
        "searched_for": location,
        "matched_location": {
            "name": selected_place.get("name"),
            "state_or_region": selected_place.get("admin1"),
            "country": selected_place.get("country"),
            "country_code": selected_place.get("country_code"),
            "latitude": latitude,
            "longitude": longitude,
        },
        "current_weather": weather_data.get("current"),
        "units": weather_data.get("current_units"),
    }


def normalize_location_query(location: str) -> str:
    cleaned = location.strip()

    # If the full user query reaches the tool, extract the part after "in".
    lower_cleaned = cleaned.lower()
    if "weather in " in lower_cleaned:
        cleaned = cleaned[lower_cleaned.rfind("weather in ") + len("weather in "):]
    elif "temperature in " in lower_cleaned:
        cleaned = cleaned[lower_cleaned.rfind("temperature in ") + len("temperature in "):]

    cleaned = cleaned.strip(" ?.!")

    compact_key = cleaned.lower().replace(" ", "")
    normal_key = cleaned.lower()

    if compact_key in LOCATION_ALIASES:
        return LOCATION_ALIASES[compact_key]

    if normal_key in LOCATION_ALIASES:
        return LOCATION_ALIASES[normal_key]

    return cleaned


def choose_best_location(
    results: list[dict],
    city: str,
    state_or_region: str,
    country: str,
) -> dict | None:
    city_clean = city.strip().lower()
    state_clean = normalize_state(state_or_region)
    country_clean = normalize_country(country)

    filtered = results

    if country_clean:
        country_filtered = [
            place
            for place in filtered
            if normalize_country(str(place.get("country", ""))) == country_clean
            or normalize_country(str(place.get("country_code", ""))) == country_clean
        ]

        if country_filtered:
            filtered = country_filtered

    if state_clean:
        state_filtered = [
            place
            for place in filtered
            if normalize_state(str(place.get("admin1", ""))) == state_clean
        ]

        if state_filtered:
            filtered = state_filtered
        else:
            # If exact state match fails, still prefer the correct country over total failure.
            if country_clean:
                return filtered[0] if filtered else None
            return None

    exact_city_matches = [
        place
        for place in filtered
        if str(place.get("name", "")).lower() == city_clean
    ]

    if exact_city_matches:
        return exact_city_matches[0]

    return filtered[0] if filtered else None


def normalize_state(value: str) -> str:
    cleaned = value.strip().lower()
    return US_STATE_ALIASES.get(cleaned, cleaned)


def normalize_country(value: str) -> str:
    cleaned = value.strip().lower()
    return COUNTRY_ALIASES.get(cleaned, cleaned)