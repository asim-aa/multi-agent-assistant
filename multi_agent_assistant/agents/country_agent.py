import json
import os
import sys
from pathlib import Path
from typing import cast

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam

from multi_agent_assistant.tools.country_tools import get_country_info
from multi_agent_assistant.prompts import COUNTRY_SYSTEM_PROMPT

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
            "name": "get_country_info",
            "description": "Get factual information about a country.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country": {
                        "type": "string",
                        "description": "Country name, for example Japan, Ireland, USA, or Iraq.",
                    }
                },
                "required": ["country"],
            },
        },
    }
]


def run_country_agent(user_prompt: str) -> str:
    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": COUNTRY_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
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
        country = extract_country_basic(user_prompt)
        result = get_country_info(country)
        return format_country_result(result)

    for tool_call in assistant_message.tool_calls:
        if tool_call.type != "function":
            continue

        function_args = json.loads(tool_call.function.arguments)

        if tool_call.function.name == "get_country_info":
            result = get_country_info(function_args["country"])
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
    return format_country_result(latest_tool_result)


def extract_country_basic(user_prompt: str) -> str:
    cleaned = (
        user_prompt.replace("?", "")
        .replace(".", "")
        .replace(",", "")
        .strip()
    )
    words = cleaned.split()

    if not words:
        return ""

    return words[-1]
def format_country_result(result: dict) -> str:
    if "error" in result:
        return result["error"]

    return (
        f"Country information for {result['name']}:\n"
        f"- Capital: {result['capital']}\n"
        f"- Region: {result['region']}\n"
        f"- Income level: {result['income_level']}\n"
        f"- Latitude: {result['latitude']}\n"
        f"- Longitude: {result['longitude']}\n"
        f"- Source: {result['source']}\n"
    )


def main() -> None:
    print("Country Agent running on SupportVectors cluster.")
    print("Ask about a country like 'Tell me about Japan'. Type quit to exit.")

    while True:
        user_input = input("\nCountry question: ").strip()

        if user_input.lower() in {"quit", "exit", "q"}:
            print("Goodbye.")
            sys.exit(0)

        if not user_input:
            print("Enter a country question.")
            continue

        answer = run_country_agent(user_input)
        print("\n" + answer)


if __name__ == "__main__":
    main()