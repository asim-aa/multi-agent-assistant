import json
import os
import sys
from pathlib import Path
from typing import cast

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam

from multi_agent_assistant.tools.time_tools import get_current_time


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

client = OpenAI(
    base_url=os.getenv("LLM_API_BASE") or os.getenv("SV_API_BASE"),
    api_key=os.getenv("LLM_API_KEY") or os.getenv("SV_API_KEY", "dummy-key"),
)

MODEL_NAME = os.getenv("LLM_MODEL") or os.getenv("SV_MODEL", "openai/gpt-oss-20b")


TIME_SYSTEM_PROMPT = """
You are a time zone assistant.

Your job:
- Use the get_current_time tool when the user asks for the current time in a location.
- Do not invent the time.
- Explain the tool result clearly.
- Include the matched location, time zone, current time, date, weekday, and UTC offset.
- If the tool returns an error, explain the issue clearly.
"""


tools: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current local time for a supported location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location name, for example Tokyo, Japan or Baghdad, Iraq.",
                    }
                },
                "required": ["location"],
            },
        },
    }
]


def run_time_agent(user_prompt: str) -> str:
    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": TIME_SYSTEM_PROMPT},
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
        location = extract_location_basic(user_prompt)
        result = get_current_time(location)
        return format_time_result(result)

    for tool_call in assistant_message.tool_calls:
        if tool_call.type != "function":
            continue

        function_args = json.loads(tool_call.function.arguments)

        if tool_call.function.name == "get_current_time":
            result = get_current_time(function_args["location"])
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
    return format_time_result(latest_tool_result)


def extract_location_basic(user_prompt: str) -> str:
    text = user_prompt.strip()

    markers = [
        "what time is it in ",
        "current time in ",
        "time in ",
    ]

    lower_text = text.lower()

    for marker in markers:
        if marker in lower_text:
            return text[lower_text.find(marker) + len(marker):].strip(" ?.!")

    return text.strip(" ?.!") if text else ""


def format_time_result(result: dict) -> str:
    if "error" in result:
        return result["error"]

    return (
        f"Current time for {result['searched_for']}:\n"
        f"- Matched location: {result['matched_location']}\n"
        f"- Time zone: {result['timezone']}\n"
        f"- Time: {result['current_time']} ({result['current_time_24h']})\n"
        f"- Date: {result['date']}\n"
        f"- Weekday: {result['weekday']}\n"
        f"- UTC offset: {result['utc_offset']}\n"
    )


def main() -> None:
    print("Time Agent running on SupportVectors cluster.")
    print("Ask for a time like 'What time is it in Tokyo?' Type quit to exit.")

    while True:
        user_input = input("\nTime question: ").strip()

        if user_input.lower() in {"quit", "exit", "q"}:
            print("Goodbye.")
            sys.exit(0)

        if not user_input:
            print("Enter a time question.")
            continue

        answer = run_time_agent(user_input)
        print("\n" + answer)


if __name__ == "__main__":
    main()