from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationReport:
    passed: bool
    warnings: list[str]


def validate_agent_result(agent_name: str, result: str) -> list[str]:
    warnings: list[str] = []

    cleaned_result = result.strip()

    if not cleaned_result:
        warnings.append(f"{agent_name} returned an empty response.")
        return warnings

    lower_result = cleaned_result.lower()

    error_indicators = [
        "error",
        "failed",
        "could not",
        "unable to",
        "not found",
        "unknown weather condition",
        "unknown weather code",
        "no valid",
    ]

    if any(indicator in lower_result for indicator in error_indicators):
        warnings.append(
            f"{agent_name} may have returned an error or incomplete result."
        )

    if agent_name == "Weather Agent":
        if (
            "temperature" not in lower_result
            and "weather" not in lower_result
            and "forecast" not in lower_result
        ):
            warnings.append(
                "Weather Agent response may be missing weather details."
            )

        if (
            "weather description" not in lower_result
            and "weather_description" not in lower_result
            and "condition" not in lower_result
        ):
            warnings.append(
                "Weather Agent response may be missing a readable weather condition."
            )

    if agent_name == "Country Agent":
        if (
            "capital" not in lower_result
            and "region" not in lower_result
            and "income" not in lower_result
            and "country" not in lower_result
        ):
            warnings.append(
                "Country Agent response may be missing country details."
            )

    if agent_name == "Time Agent":
        if (
            "current time" not in lower_result
            and "time zone" not in lower_result
            and "timezone" not in lower_result
            and "utc offset" not in lower_result
        ):
            warnings.append(
                "Time Agent response may be missing time-zone details."
            )

    return warnings


def validate_agent_results(results: list[tuple[str, str]]) -> ValidationReport:
    warnings: list[str] = []

    if not results:
        warnings.append("No agent results were produced.")
        return ValidationReport(passed=False, warnings=warnings)

    for agent_name, result in results:
        warnings.extend(validate_agent_result(agent_name, result))

    return ValidationReport(
        passed=len(warnings) == 0,
        warnings=warnings,
    )