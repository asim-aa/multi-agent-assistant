import json
import os
import sys
from pathlib import Path
from typing import cast

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam

from multi_agent_assistant.prompts import WEATHER_SYSTEM_PROMPT
from multi_agent_assistant.tools.weather_tools import get_weather


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

client = OpenAI(
    base_url=os.getenv("SV_API_BASE"),
    api_key=os.getenv("SV_API_KEY", "dummy-key"),
)

MODEL_NAME = os.getenv("SV_MODEL", "openai/gpt-oss-20b")


tools: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a structured location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": (
                            "Structured location, for example "
                            "'Dublin, California, USA' or 'Dublin, Ireland'."
                        ),
                    }
                },
                "required": ["location"],
            },
        },
    }
]


def build_location_query() -> str:
    country = input("\nCountry: ").strip()

    if not country:
        raise ValueError("Country is required.")

    city = input("City: ").strip()

    if not city:
        raise ValueError("City is required.")

    state_or_region = ""

    if country.lower() in {"usa", "us", "united states", "united states of america"}:
        state_or_region = input("State: ").strip()

        if not state_or_region:
            raise ValueError("State is required for USA locations.")

    if state_or_region:
        return f"{city}, {state_or_region}, {country}"

    return f"{city}, {country}"


def run_weather_agent(location_query: str) -> str:
    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": WEATHER_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"What is the current weather in {location_query}?",
        },
    ]

    first_response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    assistant_message = first_response.choices[0].message

    messages.append(
        cast(
            ChatCompletionMessageParam,
            assistant_message.model_dump(exclude_none=True),
        )
    )

    if not assistant_message.tool_calls:
        tool_result = get_weather(location_query)
        return format_weather_result(tool_result)

    for tool_call in assistant_message.tool_calls:
        if tool_call.type != "function":
            continue

        function_args = json.loads(tool_call.function.arguments)

        if tool_call.function.name == "get_weather":
            result = get_weather(function_args["location"])
        else:
            result = {"error": f"Unknown tool: {tool_call.function.name}"}

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result),
            }
        )

    final_response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
    )

    final_content = final_response.choices[0].message.content

    if final_content:
        return final_content

    latest_message = messages[-1]

    if latest_message.get("role") == "tool":
        latest_tool_content = latest_message.get("content", "{}")
    else:
        latest_tool_content = "{}"

    latest_tool_result = json.loads(str(latest_tool_content))
    return format_weather_result(latest_tool_result)


def format_weather_result(result: dict) -> str:
    if "error" in result:
        return result["error"]

    location = result["matched_location"]
    weather = result["current_weather"]
    units = result["units"]

    return (
        f"Current weather for {location['name']}, "
        f"{location.get('state_or_region')}, {location['country']}:\n"
        f"- Temperature: {weather['temperature_2m']} {units['temperature_2m']}\n"
        f"- Feels like: {weather['apparent_temperature']} "
        f"{units['apparent_temperature']}\n"
        f"- Wind speed: {weather['wind_speed_10m']} {units['wind_speed_10m']}\n"
        f"- Precipitation: {weather['precipitation']} {units['precipitation']}\n"
        f"- Weather code: {weather['weather_code']}\n"
    )


def main() -> None:
    print("Weather Agent running on SupportVectors cluster.")
    print("Type location details when prompted. Type 'quit' as country to exit.")

    while True:
        try:
            country_check = input("\nStart? Press Enter or type quit: ").strip()

            if country_check.lower() in {"quit", "exit", "q"}:
                print("Goodbye.")
                sys.exit(0)

            location_query = build_location_query()
            answer = run_weather_agent(location_query)
            print("\n" + answer)

        except ValueError as error:
            print(f"Input error: {error}")

        except Exception as error:
            print(f"Unexpected error: {error}")


if __name__ == "__main__":
    main()