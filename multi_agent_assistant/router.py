import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam


@dataclass
class RouteDecision:
    route: str
    agent_name: str
    reason: str
    weather_query: str | None = None
    country_query: str | None = None
    time_query: str | None = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

client = OpenAI(
    base_url=os.getenv("LLM_API_BASE") or os.getenv("SV_API_BASE"),
    api_key=os.getenv("LLM_API_KEY") or os.getenv("SV_API_KEY", "dummy-key"),
)

MODEL_NAME = os.getenv("LLM_MODEL") or os.getenv("SV_MODEL", "openai/gpt-oss-20b")


ROUTER_SYSTEM_PROMPT = """
You are a router agent for a multi-agent assistant.

Available routes:
- weather: for weather, temperature, rain, wind, forecast, or current conditions.
- country: for country facts, capital, region, income level, or general country information.
- time: for current time, local time, clock, timezone, or time zone questions.
- multi: when the user asks for more than one supported task.
- unknown: when the request does not fit.

Return ONLY valid JSON with this exact schema:
{
  "route": "weather | country | time | multi | unknown",
  "agent_name": "Weather Agent | Country Agent | Time Agent | Weather Agent + Country Agent | Weather Agent + Time Agent | Country Agent + Time Agent | Weather Agent + Country Agent + Time Agent | None",
  "reason": "brief reason",
  "weather_query": "clean weather query or null",
  "country_query": "clean country query or null",
  "time_query": "clean time query or null"
}

Rules:
- If route is weather, fill weather_query and set country_query and time_query to null.
- If route is country, fill country_query and set weather_query and time_query to null.
- If route is time, fill time_query and set weather_query and country_query to null.
- If route is multi, fill every relevant query field and set unused fields to null.
- For weather_query, write a clean query like: "What is the weather in Tokyo, Japan?"
- For country_query, write a clean query like: "Tell me about Japan"
- For time_query, write a clean query like: "What time is it in Tokyo, Japan?"
- If the user says "there" in a time query after mentioning a location, resolve "there" to the mentioned location.
- Do not include markdown.
- Do not include explanations outside JSON.
"""


def route_request(user_input: str) -> RouteDecision:
    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0,
    )

    content = response.choices[0].message.content

    if not content:
        return fallback_route(user_input)

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return fallback_route(user_input)

    route = data.get("route", "unknown")

    if route not in {"weather", "country", "time", "multi", "unknown"}:
        route = "unknown"

    return RouteDecision(
        route=route,
        agent_name=data.get("agent_name", "None"),
        reason=data.get("reason", "LLM router classified the request."),
        weather_query=data.get("weather_query"),
        country_query=data.get("country_query"),
        time_query=data.get("time_query"),
    )


def fallback_route(user_input: str) -> RouteDecision:
    text = user_input.lower()

    has_weather = any(
        word in text
        for word in ["weather", "temperature", "rain", "wind", "forecast"]
    )

    has_country = any(
        word in text
        for word in ["country", "capital", "region", "population", "tell me about"]
    )

    has_time = any(
        word in text
        for word in ["time", "timezone", "time zone", "clock"]
    )

    detected_routes: list[str] = []

    if has_country:
        detected_routes.append("country")

    if has_weather:
        detected_routes.append("weather")

    if has_time:
        detected_routes.append("time")

    if len(detected_routes) > 1:
        return RouteDecision(
            route="multi",
            agent_name=" + ".join(get_agent_name(route) for route in detected_routes),
            reason="Fallback router detected multiple supported intents.",
            country_query=user_input if has_country else None,
            weather_query=user_input if has_weather else None,
            time_query=user_input if has_time else None,
        )

    if has_weather:
        return RouteDecision(
            route="weather",
            agent_name="Weather Agent",
            reason="Fallback router detected weather keywords.",
            weather_query=user_input,
        )

    if has_country:
        return RouteDecision(
            route="country",
            agent_name="Country Agent",
            reason="Fallback router detected country keywords.",
            country_query=user_input,
        )

    if has_time:
        return RouteDecision(
            route="time",
            agent_name="Time Agent",
            reason="Fallback router detected time-related keywords.",
            time_query=user_input,
        )

    return RouteDecision(
        route="unknown",
        agent_name="None",
        reason="No supported intent detected.",
    )


def get_agent_name(route: str) -> str:
    names = {
        "weather": "Weather Agent",
        "country": "Country Agent",
        "time": "Time Agent",
    }

    return names.get(route, route.title())