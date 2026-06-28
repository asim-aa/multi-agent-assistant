import requests


def get_country_info(country: str) -> dict:
    country = country.strip()

    if not country:
        return {"error": "Country name is required."}

    country_codes = {
        "iraq": "IRQ",
        "japan": "JPN",
        "ireland": "IRL",
        "united states": "USA",
        "usa": "USA",
        "canada": "CAN",
        "india": "IND",
        "pakistan": "PAK",
        "saudi arabia": "SAU",
        "united kingdom": "GBR",
        "uk": "GBR",
        "france": "FRA",
        "germany": "DEU",
    }

    code = country_codes.get(country.lower())

    if not code:
        return {
            "error": (
                f"Country '{country}' is not in the local code map yet. "
                "Add it to country_codes in country_tools.py."
            )
        }

    url = f"https://api.worldbank.org/v2/country/{code}"
    params = {"format": "json"}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as error:
        return {"error": f"World Bank API request failed: {error}"}

    data = response.json()

    if not isinstance(data, list) or len(data) < 2 or not data[1]:
        return {"error": f"No country found for: {country}"}

    country_data = data[1][0]

    return {
        "searched_for": country,
        "name": country_data.get("name"),
        "capital": country_data.get("capitalCity") or "Unknown",
        "region": country_data.get("region", {}).get("value"),
        "income_level": country_data.get("incomeLevel", {}).get("value"),
        "longitude": country_data.get("longitude"),
        "latitude": country_data.get("latitude"),
        "source": "World Bank Country API",
    }