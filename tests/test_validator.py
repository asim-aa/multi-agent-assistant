from multi_agent_assistant.validators import (
    validate_agent_result,
    validate_agent_results,
)


def test_validator_passes_good_agent_outputs():
    results = [
        (
            "Country Agent",
            "India has capital New Delhi, region South Asia, and income level Lower middle income.",
        ),
        (
            "Weather Agent",
            "Temperature is 70 F. Weather description is Partly cloudy.",
        ),
        (
            "Time Agent",
            "Current time is 04:36 AM. Time zone is Asia/Kolkata. UTC offset is +05:30.",
        ),
    ]

    report = validate_agent_results(results)

    assert report.passed is True
    assert report.warnings == []


def test_validator_warns_on_empty_result():
    warnings = validate_agent_result("Weather Agent", "")

    assert warnings
    assert "empty response" in warnings[0].lower()


def test_validator_warns_on_error_text():
    warnings = validate_agent_result(
        "Weather Agent",
        "Weather Agent failed with RequestException.",
    )

    assert warnings
    assert "error or incomplete" in warnings[0].lower()


def test_validator_warns_when_no_results_exist():
    report = validate_agent_results([])

    assert report.passed is False
    assert "No agent results were produced." in report.warnings
