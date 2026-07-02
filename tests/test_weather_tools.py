from multi_agent_assistant.tools.weather_tools import (
    choose_best_location,
    get_population_score,
    normalize_country,
    normalize_location_query,
    normalize_state,
    parse_weather_code,
    score_location,
)


def test_normalize_bangalore_alias():
    assert normalize_location_query("Bangalore") == "Bengaluru, Karnataka, India"


def test_normalize_weather_in_query():
    assert normalize_location_query("What is the weather in Bangalore?") == (
        "Bengaluru, Karnataka, India"
    )


def test_normalize_dublin_ca_alias():
    assert normalize_location_query("Dublin, CA") == "Dublin, California, USA"


def test_parse_weather_code_int():
    assert parse_weather_code(3) == 3


def test_parse_weather_code_float():
    assert parse_weather_code(3.0) == 3


def test_parse_weather_code_string():
    assert parse_weather_code("3") == 3


def test_parse_weather_code_invalid_string():
    assert parse_weather_code("bad") is None


def test_parse_weather_code_bool_rejected():
    assert parse_weather_code(True) is None


def test_normalize_state_alias():
    assert normalize_state("CA") == "california"


def test_normalize_country_alias_usa():
    assert normalize_country("USA") == "united states"


def test_normalize_country_code_india():
    assert normalize_country("IN") == "india"


def test_population_score_large_city():
    place = {"population": 8_000_000}
    assert get_population_score(place) == 10


def test_population_score_medium_city():
    place = {"population": 250_000}
    assert get_population_score(place) == 5


def test_population_score_missing_population():
    place = {}
    assert get_population_score(place) == 0


def test_score_location_exact_bengaluru_match():
    place = {
        "name": "Bengaluru",
        "admin1": "Karnataka",
        "country": "India",
        "country_code": "IN",
        "population": 8_443_675,
    }

    assert score_location(
        place=place,
        city="Bengaluru",
        state_or_region="Karnataka",
        country="India",
    ) == 130


def test_choose_best_location_prefers_dublin_california_when_state_given():
    results = [
        {
            "name": "Dublin",
            "admin1": "Leinster",
            "country": "Ireland",
            "country_code": "IE",
            "population": 544_107,
        },
        {
            "name": "Dublin",
            "admin1": "California",
            "country": "United States",
            "country_code": "US",
            "population": 72_000,
        },
    ]

    selected = choose_best_location(
        results=results,
        city="Dublin",
        state_or_region="California",
        country="USA",
    )

    assert selected is not None
    assert selected["country"] == "United States"
    assert selected["admin1"] == "California"
