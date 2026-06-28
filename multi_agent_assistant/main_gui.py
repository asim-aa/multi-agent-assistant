import threading
import tkinter as tk
from tkinter import scrolledtext
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


class MultiAgentAssistantGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Multi-Agent Assistant")
        self.root.geometry("950x700")

        self.build_ui()

    def build_ui(self) -> None:
        title_label = tk.Label(
            self.root,
            text="Multi-Agent Assistant",
            font=("Arial", 22, "bold"),
        )
        title_label.pack(pady=(15, 5))

        subtitle_label = tk.Label(
            self.root,
            text="Ask about weather, countries, time, or combinations of them.",
            font=("Arial", 12),
        )
        subtitle_label.pack(pady=(0, 15))

        input_frame = tk.Frame(self.root)
        input_frame.pack(fill="x", padx=20)

        self.input_box = tk.Entry(input_frame, font=("Arial", 14))
        self.input_box.pack(side="left", fill="x", expand=True, ipady=8)


        self.input_box.bind("<Return>", lambda event: self.run_assistant())

        self.run_button = tk.Button(
            input_frame,
            text="Run",
            font=("Arial", 12, "bold"),
            command=self.run_assistant,
            width=10,
        )
        self.run_button.pack(side="right", padx=(10, 0), ipady=6)

        example_label = tk.Label(
            self.root,
            text="Example: Tell me about Japan, what is the weather in Tokyo, and what time is it there?",
            font=("Arial", 10),
            fg="gray",
        )
        example_label.pack(anchor="w", padx=20, pady=(8, 10))

        output_label = tk.Label(
            self.root,
            text="Output",
            font=("Arial", 14, "bold"),
        )
        output_label.pack(anchor="w", padx=20)

        self.output_box = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            font=("Menlo", 12),
            height=28,
        )
        self.output_box.pack(fill="both", expand=True, padx=20, pady=(5, 20))

    def run_assistant(self) -> None:
        user_input = self.input_box.get().strip()

        if not user_input:
            self.write_output("Please enter a question.")
            return

        self.run_button.config(state="disabled", text="Running...")
        self.write_output("Running assistant...\n")

        thread = threading.Thread(
            target=self.process_request,
            args=(user_input,),
            daemon=True,
        )
        thread.start()

    def process_request(self, user_input: str) -> None:
        try:
            output = self.generate_response(user_input)
        except Exception as error:
            output = f"Unexpected error:\n{error}"
        finally:
            self.root.after(0, lambda: self.run_button.config(state="normal"))

        self.root.after(0, lambda: self.run_button.config(state="normal", text="Run"))

    def generate_response(self, user_input: str) -> str:
        decision = route_request(user_input)

        lines: list[str] = []

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("Decision Pipeline")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"User request: {user_input}")
        lines.append(f"Router decision: {decision.route}")
        lines.append(f"Selected agent(s): {decision.agent_name}")
        lines.append(f"Reason: {decision.reason}")

        if decision.country_query:
            lines.append(f"Country sub-query: {decision.country_query}")

        if decision.weather_query:
            lines.append(f"Weather sub-query: {decision.weather_query}")

        if decision.time_query:
            lines.append(f"Time sub-query: {decision.time_query}")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")

        agents_to_run = get_agents_to_run(decision)

        if not agents_to_run:
            lines.append("Final Answer:")
            lines.append(
                "I can route weather, country-information, and time questions right now.\n"
                "Try: 'What is the weather in Tokyo?', "
                "'Tell me about Japan.', or "
                "'What time is it in Tokyo?'"
            )
            return "\n".join(lines)

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("Executing Agents")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        results: list[str] = []

        for agent_key in agents_to_run:
            agent_name = get_agent_display_name(agent_key)
            agent_query = get_agent_query(agent_key, decision, user_input)
            agent_function = AGENTS[agent_key]

            lines.append(f"✓ {agent_name} running")
            lines.append(f"  Query: {agent_query}")

            agent_answer = agent_function(agent_query)
            results.append(f"{agent_name} Result:\n{agent_answer}")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")
        lines.append("Final Answer:")
        lines.append("")
        lines.append("\n\n".join(results))

        return "\n".join(lines)

    def write_output(self, text: str) -> None:
        self.output_box.delete("1.0", tk.END)
        self.output_box.insert(tk.END, text)


def main() -> None:
    root = tk.Tk()
    app = MultiAgentAssistantGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()