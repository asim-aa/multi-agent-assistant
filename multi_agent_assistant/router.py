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


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

client = OpenAI(
    base_url=os.getenv("SV_API_BASE"),
    api_key=os.getenv("SV_API_KEY", "dummy-key"),
)

MODEL_NAME = os.getenv("SV_MODEL", "openai/gpt-oss-20b")


ROUTER_SYSTEM_PROMPT = """
You are a router agent for a multi-agent assistant.

Available routes:
- weather: for weather, temperature, rain, wind, forecast, or current conditions.
- country: for country facts, capital, region, income level, or general country information.
- multi: when the user asks for both weather and country information.
- unknown: when the request does not fit.

Return ONLY valid JSON with this exact schema:
{
  "route": "weather | country | multi | unknown",
  "agent_name": "Weather Agent | Country Agent | Weather Agent + Country Agent | None",
  "reason": "brief reason",
  "weather_query": "clean weather query or null",
  "country_query": "clean country query or null"
}

Rules:
- If route is weather, fill weather_query and set country_query to null.
- If route is country, fill country_query and set weather_query to null.
- If route is multi, fill both weather_query and country_query.
- For weather_query, write a clean query like: "What is the weather in Tokyo, Japan?"
- For country_query, write a clean query like: "Tell me about Japan"
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

    if route not in {"weather", "country", "multi", "unknown"}:
        route = "unknown"

    return RouteDecision(
        route=route,
        agent_name=data.get("agent_name", "None"),
        reason=data.get("reason", "LLM router classified the request."),
        weather_query=data.get("weather_query"),
        country_query=data.get("country_query"),
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

    if has_weather and has_country:
        return RouteDecision(
            route="multi",
            agent_name="Weather Agent + Country Agent",
            reason="Fallback router detected both weather and country keywords.",
            weather_query=user_input,
            country_query=user_input,
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

    return RouteDecision(
        route="unknown",
        agent_name="None",
        reason="No supported intent detected.",
    )