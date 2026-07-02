import sys
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from multi_agent_assistant.agents.country_agent import run_country_agent
from multi_agent_assistant.agents.time_agent import run_time_agent
from multi_agent_assistant.agents.weather_agent import run_weather_agent
from multi_agent_assistant.router import RouteDecision, route_request


AgentFunction = Callable[[str], str]


@dataclass(frozen=True)
class ValidationReport:
    passed: bool
    warnings: list[str]


def validate_agent_results(results: list[tuple[str, str]]) -> ValidationReport:
    warnings: list[str] = []
    
    if not results:
        warnings.append("No agent results to validate.")
    
    for agent_name, agent_answer in results:
        if not agent_answer or not agent_answer.strip():
            warnings.append(f"{agent_name} returned empty result.")
        if "failed" in agent_answer.lower() or "error" in agent_answer.lower():
            warnings.append(f"{agent_name} may have encountered an error.")
    
    return ValidationReport(passed=len(warnings) == 0, warnings=warnings)


AGENTS: dict[str, AgentFunction] = {
    "weather": run_weather_agent,
    "country": run_country_agent,
    "time": run_time_agent,
}


@dataclass(frozen=True)
class AgentTask:
    key: str
    name: str
    query: str
    function: AgentFunction


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


def build_agent_tasks(
    agents_to_run: list[str],
    decision: RouteDecision,
    user_input: str,
) -> list[AgentTask]:
    tasks: list[AgentTask] = []

    for agent_key in agents_to_run:
        agent_function = AGENTS.get(agent_key)

        if agent_function is None:
            continue

        tasks.append(
            AgentTask(
                key=agent_key,
                name=get_agent_display_name(agent_key),
                query=get_agent_query(agent_key, decision, user_input),
                function=agent_function,
            )
        )

    return tasks


def run_agent_tasks_parallel(tasks: list[AgentTask]) -> list[tuple[str, str]]:
    if not tasks:
        return []

    results_by_key: dict[str, tuple[str, str]] = {}

    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        future_to_task: dict[Future[str], AgentTask] = {
            executor.submit(task.function, task.query): task
            for task in tasks
        }

        for future in as_completed(future_to_task):
            task = future_to_task[future]

            try:
                agent_answer = future.result()
            except Exception as error:
                agent_answer = (
                    f"{task.name} failed with "
                    f"{type(error).__name__}: {error}"
                )

            results_by_key[task.key] = (task.name, agent_answer)

    ordered_results: list[tuple[str, str]] = []

    for task in tasks:
        result = results_by_key.get(task.key)

        if result is not None:
            ordered_results.append(result)

    return ordered_results


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


def print_validation_layer(results: list[tuple[str, str]]) -> None:
    validation_report = validate_agent_results(results)

    print("\nValidation Layer")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if validation_report.passed:
        print("✓ All agent outputs passed validation.")
    else:
        print("⚠ Validation warnings found:")

        for warning in validation_report.warnings:
            print(f"- {warning}")

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


def format_final_answer(results: list[tuple[str, str]]) -> str:
    return "\n\n".join(
        f"{agent_name} Result:\n{agent_answer}"
        for agent_name, agent_answer in results
    )


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

        tasks = build_agent_tasks(
            agents_to_run=agents_to_run,
            decision=decision,
            user_input=user_input,
        )

        if not tasks:
            print("\nFinal Answer:")
            print("No valid agent tasks could be created.")
            continue

        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("Executing Agents in Parallel")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        for task in tasks:
            print(f"✓ {task.name} started")
            print(f"  Query: {task.query}")

        results = run_agent_tasks_parallel(tasks)

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        print_validation_layer(results)

        answer = format_final_answer(results)

        print("\nFinal Answer:")
        print(answer)


if __name__ == "__main__":
    main()