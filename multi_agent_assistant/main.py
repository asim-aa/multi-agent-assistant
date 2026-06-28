import sys
from collections.abc import Callable

from multi_agent_assistant.agents.country_agent import run_country_agent
from multi_agent_assistant.agents.time_agent import run_time_agent
from multi_agent_assistant.agents.weather_agent import run_weather_agent
from multi_agent_assistant.router import RouteDecision, route_request


AgentFunction = Callable[[str], str]


AGENTS: dict[str, AgentFunction] = {
    "weather": run_weather_agent,
    "country": run_country_agent,
    "time": run_time_agent,
}


def get_agent_query(agent_key: str, decision: RouteDecision, user_input: str) -> str:
    if agent_key == "weather":
        return decision.weather_query or user_input

    if agent_key == "country":
        return decision.country_query or user_input

    if agent_key == "time":
        return decision.time_query or user_input

    return user_input


def get_agent_display_name(agent_key: str) -> str:
    names = {
        "weather": "Weather Agent",
        "country": "Country Agent",
        "time": "Time Agent",
    }

    return names.get(agent_key, agent_key.title())


def get_agents_to_run(decision: RouteDecision) -> list[str]:
    agents: list[str] = []

    if decision.country_query:
        agents.append("country")

    if decision.weather_query:
        agents.append("weather")

    if decision.time_query:
        agents.append("time")

    if agents:
        return agents

    if decision.route in AGENTS:
        return [decision.route]

    return []


def print_decision_pipeline(user_input: str, decision: RouteDecision) -> None:
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Decision Pipeline")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"User request: {user_input}")
    print(f"Router decision: {decision.route}")
    print(f"Selected agent(s): {decision.agent_name}")
    print(f"Reason: {decision.reason}")

    if decision.country_query:
        print(f"Country sub-query: {decision.country_query}")

    if decision.weather_query:
        print(f"Weather sub-query: {decision.weather_query}")

    if decision.time_query:
        print(f"Time sub-query: {decision.time_query}")

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


def main() -> None:
    print("Multi-Agent Assistant running on SupportVectors cluster.")
    print("Ask about weather, countries, time, or combinations of them.")
    print("Type quit to exit.")

    while True:
        user_input = input("\nAsk: ").strip()

        if user_input.lower() in {"quit", "exit", "q"}:
            print("Goodbye.")
            sys.exit(0)

        if not user_input:
            print("Enter a question.")
            continue

        decision = route_request(user_input)
        print_decision_pipeline(user_input, decision)

        agents_to_run = get_agents_to_run(decision)

        if not agents_to_run:
            print("\nFinal Answer:")
            print(
                "I can route weather, country-information, and time questions right now. "
                "Try: 'What is the weather in Tokyo?', "
                "'Tell me about Japan.', or "
                "'What time is it in Tokyo?'"
            )
            continue

        results: list[str] = []

        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("Executing Agents")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        for agent_key in agents_to_run:
            agent_name = get_agent_display_name(agent_key)
            agent_query = get_agent_query(agent_key, decision, user_input)
            agent_function = AGENTS[agent_key]

            print(f"✓ {agent_name} running")
            print(f"  Query: {agent_query}")

            agent_answer = agent_function(agent_query)

            results.append(f"{agent_name} Result:\n{agent_answer}")

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        answer = "\n\n".join(results)

        print("\nFinal Answer:")
        print(answer)


if __name__ == "__main__":
    main()