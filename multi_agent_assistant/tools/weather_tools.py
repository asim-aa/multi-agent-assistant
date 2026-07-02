from typing import Any

import requests


US_STATE_ALIASES: dict[str, str] = {
    "ca": "california",
    "california": "california",
    "ny": "new york",
    "new york": "new york",
    "tx": "texas",
    "texas": "texas",
    "fl": "florida",
    "florida": "florida",
}


COMMON_LOCATION_ALIASES: dict[str, str] = {
    "tokyo": "Tokyo, Tokyo, Japan",
    "tokyo japan": "Tokyo, Tokyo, Japan",
    "tokyo, japan": "Tokyo, Tokyo, Japan",
    "tokyo,japan": "Tokyo, Tokyo, Japan",

    "dublin ca": "Dublin, California, USA",
    "dublin, ca": "Dublin, California, USA",
    "dublin,ca": "Dublin, California, USA",
    "dublin california": "Dublin, California, USA",
    "dublin, california": "Dublin, California, USA",
    "dublin,california": "Dublin, California, USA",

    "bangalore": "Bengaluru, Karnataka, India",
    "bangalore india": "Bengaluru, Karnataka, India",
    "bangalore, india": "Bengaluru, Karnataka, India",
    "bangalore,india": "Bengaluru, Karnataka, India",
    "bangalore karnataka india": "Bengaluru, Karnataka, India",
    "bangalore, karnataka, india": "Bengaluru, Karnataka, India",
    "bangalore,karnataka,india": "Bengaluru, Karnataka, India",

    "bengaluru": "Bengaluru, Karnataka, India",
    "bengaluru india": "Bengaluru, Karnataka, India",
    "bengaluru, india": "Bengaluru, Karnataka, India",
    "bengaluru,india": "Bengaluru, Karnataka, India",
    "bengaluru karnataka india": "Bengaluru, Karnataka, India",
    "bengaluru, karnataka, india": "Bengaluru, Karnataka, India",
    "bengaluru,karnataka,india": "Bengaluru, Karnataka, India",
}


COUNTRY_ALIASES: dict[str, str] = {
    "usa": "united states",
    "us": "united states",
    "u.s.": "united states",
    "u.s.a.": "united states",
    "united states of america": "united states",
    "united states": "united states",
    "japan": "japan",
    "jp": "japan",
    "ireland": "ireland",
    "ie": "ireland",
    "india": "india",
    "in": "india",
}


WMO_WEATHER_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def get_weather(location: str) -> dict[str, Any]:
    location = normalize_location_query(location)

    parts = [part.strip() for part in location.split(",")]

    city = parts[0] if len(parts) > 0 else location
    state_or_region = parts[1] if len(parts) > 1 else ""
    country = parts[2] if len(parts) > 2 else ""

    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo_params: dict[str, Any] = {
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

    geo_data: dict[str, Any] = geo_response.json()
    raw_results = geo_data.get("results", [])

    if not isinstance(raw_results, list) or not raw_results:
        return {"error": f"Could not find city: {city}"}

    results: list[dict[str, Any]] = [
        result for result in raw_results if isinstance(result, dict)
    ]

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
                "population": place.get("population"),
            }
            for place in results[:10]
        ]

        return {
            "error": f"Could not confidently match location: {location}",
            "available_matches": available_matches,
        }

    latitude = selected_place.get("latitude")
    longitude = selected_place.get("longitude")

    if latitude is None or longitude is None:
        return {
            "error": f"Matched location is missing latitude or longitude: {location}",
            "matched_location": selected_place,
        }

    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_params: dict[str, Any] = {
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

    weather_data: dict[str, Any] = weather_response.json()
    raw_current_weather = weather_data.get("current", {})

    if isinstance(raw_current_weather, dict):
        current_weather: dict[str, Any] = dict(raw_current_weather)
    else:
        current_weather = {}

    raw_weather_code = current_weather.get("weather_code")
    weather_code = parse_weather_code(raw_weather_code)

    if weather_code is None:
        weather_description = "Unknown weather condition"
    else:
        weather_description = WMO_WEATHER_CODES.get(
            weather_code,
            f"Unknown weather code: {weather_code}",
        )

    current_weather["weather_code"] = weather_code
    current_weather["weather_description"] = weather_description
    current_weather["weather_code_description"] = weather_description

    return {
        "searched_for": location,
        "matched_location": {
            "name": selected_place.get("name"),
            "state_or_region": selected_place.get("admin1"),
            "country": selected_place.get("country"),
            "country_code": selected_place.get("country_code"),
            "latitude": latitude,
            "longitude": longitude,
            "population": selected_place.get("population"),
            "location_match_score": score_location(
                place=selected_place,
                city=city,
                state_or_region=state_or_region,
                country=country,
            ),
        },
        "current_weather": current_weather,
        "units": weather_data.get("current_units"),
    }


def normalize_location_query(location: str) -> str:
    cleaned = location.strip()
    lower_cleaned = cleaned.lower()

    if "weather in " in lower_cleaned:
        cleaned = cleaned[lower_cleaned.rfind("weather in ") + len("weather in "):]
    elif "temperature in " in lower_cleaned:
        cleaned = cleaned[
            lower_cleaned.rfind("temperature in ") + len("temperature in "):
        ]

    cleaned = cleaned.strip(" ?.!")

    normal_key = cleaned.lower()
    compact_key = normal_key.replace(" ", "")

    if normal_key in COMMON_LOCATION_ALIASES:
        return COMMON_LOCATION_ALIASES[normal_key]

    if compact_key in COMMON_LOCATION_ALIASES:
        return COMMON_LOCATION_ALIASES[compact_key]

    return cleaned


def choose_best_location(
    results: list[dict[str, Any]],
    city: str,
    state_or_region: str,
    country: str,
) -> dict[str, Any] | None:
    if not results:
        return None

    scored_results = [
        (
            score_location(
                place=place,
                city=city,
                state_or_region=state_or_region,
                country=country,
            ),
            get_population_score(place),
            place,
        )
        for place in results
    ]

    scored_results.sort(
        key=lambda item: (
            item[0],
            item[1],
        ),
        reverse=True,
    )

    best_score, _, best_place = scored_results[0]

    if best_score <= 0:
        return None

    return best_place


def score_location(
    place: dict[str, Any],
    city: str,
    state_or_region: str,
    country: str,
) -> int:
    score = 0

    place_name = str(place.get("name", "")).strip().lower()
    place_state = normalize_state(str(place.get("admin1", "")))
    place_country = normalize_country(str(place.get("country", "")))
    place_country_code = normalize_country(str(place.get("country_code", "")))

    city_clean = city.strip().lower()
    state_clean = normalize_state(state_or_region)
    country_clean = normalize_country(country)

    if place_name == city_clean:
        score += 50

    if country_clean and (
        place_country == country_clean or place_country_code == country_clean
    ):
        score += 40

    if state_clean and place_state == state_clean:
        score += 30

    score += get_population_score(place)

    return score


def get_population_score(place: dict[str, Any]) -> int:
    population = place.get("population")

    if not isinstance(population, int):
        return 0

    if population > 1_000_000:
        return 10

    if population > 100_000:
        return 5

    return 0


def parse_weather_code(value: Any) -> int | None:
    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None

    return None


def normalize_state(value: str) -> str:
    cleaned = value.strip().lower()
    return US_STATE_ALIASES.get(cleaned, cleaned)


def normalize_country(value: str) -> str:
    cleaned = value.strip().lower()
    return COUNTRY_ALIASES.get(cleaned, cleaned)