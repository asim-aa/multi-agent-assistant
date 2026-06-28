import threading
import tkinter as tk
from collections.abc import Callable
from tkinter import scrolledtext

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
        self.root.geometry("1100x800")
        self.root.configure(bg="#0f172a")

        self.bg = "#0f172a"
        self.panel_bg = "#111827"
        self.input_bg = "#ffffff"
        self.text_bg = "#020617"
        self.text_fg = "#e5e7eb"
        self.muted = "#94a3b8"
        self.accent = "#38bdf8"
        self.success = "#22c55e"
        self.warning = "#facc15"
        self.error = "#f87171"

        self.build_ui()

    def build_ui(self) -> None:
        header_frame = tk.Frame(self.root, bg=self.bg)
        header_frame.pack(fill="x", padx=24, pady=(20, 10))

        title_label = tk.Label(
            header_frame,
            text="Multi-Agent Assistant",
            font=("Arial", 26, "bold"),
            fg="#f8fafc",
            bg=self.bg,
        )
        title_label.pack(anchor="w")

        subtitle_label = tk.Label(
            header_frame,
            text="Ask about weather, countries, time, or combinations of them.",
            font=("Arial", 13),
            fg=self.muted,
            bg=self.bg,
        )
        subtitle_label.pack(anchor="w", pady=(4, 0))

        input_panel = tk.Frame(self.root, bg=self.panel_bg, padx=14, pady=14)
        input_panel.pack(fill="x", padx=24, pady=(8, 10))

        self.input_box = tk.Entry(
            input_panel,
            font=("Arial", 15),
            bg=self.input_bg,
            fg="#111827",
            relief="flat",
        )
        self.input_box.pack(side="left", fill="x", expand=True, ipady=10)
        self.input_box.bind("<Return>", lambda event: self.run_assistant())

        self.run_button = tk.Button(
            input_panel,
            text="Run",
            font=("Arial", 12, "bold"),
            command=self.run_assistant,
            width=10,
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
        )
        self.run_button.pack(side="right", padx=(10, 0), ipady=8)

        self.clear_button = tk.Button(
            input_panel,
            text="Clear",
            font=("Arial", 12),
            command=self.clear_output,
            width=8,
            bg="#334155",
            fg="white",
            activebackground="#475569",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
        )
        self.clear_button.pack(side="right", padx=(10, 0), ipady=8)

        example_label = tk.Label(
            self.root,
            text=(
                "Example: Tell me about Japan, what is the weather in Tokyo, "
                "and what time is it there?"
            ),
            font=("Arial", 10),
            fg=self.muted,
            bg=self.bg,
        )
        example_label.pack(anchor="w", padx=26, pady=(0, 12))

        output_header = tk.Frame(self.root, bg=self.bg)
        output_header.pack(fill="x", padx=24)

        output_label = tk.Label(
            output_header,
            text="Output",
            font=("Arial", 15, "bold"),
            fg="#f8fafc",
            bg=self.bg,
        )
        output_label.pack(side="left")

        status_label = tk.Label(
            output_header,
            text="Decision pipeline + agent responses",
            font=("Arial", 10),
            fg=self.muted,
            bg=self.bg,
        )
        status_label.pack(side="right")

        self.output_box = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            font=("Menlo", 12),
            bg=self.text_bg,
            fg=self.text_fg,
            insertbackground=self.text_fg,
            relief="flat",
            borderwidth=0,
            height=30,
            padx=16,
            pady=16,
        )
        self.output_box.pack(fill="both", expand=True, padx=24, pady=(8, 24))

        self.configure_output_tags()
        self.output_box.configure(state="disabled")

        self.input_box.focus_set()

    def configure_output_tags(self) -> None:
        self.output_box.tag_configure(
            "section",
            foreground="#f8fafc",
            font=("Menlo", 14, "bold"),
            spacing1=10,
            spacing3=6,
        )
        self.output_box.tag_configure(
            "agent",
            foreground=self.accent,
            font=("Menlo", 13, "bold"),
            spacing1=8,
            spacing3=4,
        )
        self.output_box.tag_configure(
            "label",
            foreground="#93c5fd",
            font=("Menlo", 12, "bold"),
        )
        self.output_box.tag_configure(
            "success",
            foreground=self.success,
            font=("Menlo", 12, "bold"),
        )
        self.output_box.tag_configure(
            "warning",
            foreground=self.warning,
            font=("Menlo", 12, "bold"),
        )
        self.output_box.tag_configure(
            "error",
            foreground=self.error,
            font=("Menlo", 12, "bold"),
        )
        self.output_box.tag_configure(
            "muted",
            foreground=self.muted,
        )
        self.output_box.tag_configure(
            "table",
            foreground="#d1d5db",
            font=("Menlo", 11),
        )
        self.output_box.tag_configure(
            "body",
            foreground=self.text_fg,
            font=("Menlo", 12),
            spacing3=2,
        )

    def run_assistant(self) -> None:
        if str(self.run_button["state"]) == "disabled":
            return

        user_input = self.input_box.get().strip()

        if not user_input:
            self.write_output("Please enter a question.")
            return

        self.clear_output()
        self.run_button.config(state="disabled", text="Running...")
        self.safe_insert_line("Running assistant...", "muted")

        thread = threading.Thread(
            target=self.process_request,
            args=(user_input,),
            daemon=True,
        )
        thread.start()

    def process_request(self, user_input: str) -> None:
        try:
            self.safe_insert_line("Routing request...", "muted")
            decision = route_request(user_input)

            self.safe_insert_blank()
            self.safe_insert_section("Decision Pipeline")
            self.safe_insert_line(f"User request: {user_input}", "label")
            self.safe_insert_line(f"Router decision: {decision.route}", "label")
            self.safe_insert_line(f"Selected agent(s): {decision.agent_name}", "label")
            self.safe_insert_line(f"Reason: {decision.reason}", "label")

            if decision.country_query:
                self.safe_insert_line(f"Country sub-query: {decision.country_query}", "label")

            if decision.weather_query:
                self.safe_insert_line(f"Weather sub-query: {decision.weather_query}", "label")

            if decision.time_query:
                self.safe_insert_line(f"Time sub-query: {decision.time_query}", "label")

            agents_to_run = get_agents_to_run(decision)

            if not agents_to_run:
                self.safe_insert_blank()
                self.safe_insert_section("Final Answer")
                self.safe_insert_line(
                    "I can route weather, country-information, and time questions right now."
                )
                self.safe_insert_line(
                    "Try: 'What is the weather in Tokyo?', "
                    "'Tell me about Japan.', or "
                    "'What time is it in Tokyo?'"
                )
                return

            self.safe_insert_blank()
            self.safe_insert_section("Executing Agents")

            results: list[tuple[str, str]] = []

            for agent_key in agents_to_run:
                agent_name = get_agent_display_name(agent_key)
                agent_query = get_agent_query(agent_key, decision, user_input)
                agent_function = AGENTS[agent_key]

                self.safe_insert_line(f"✓ {agent_name} running", "success")
                self.safe_insert_line(f"Query: {agent_query}", "muted")

                agent_answer = agent_function(agent_query)

                self.safe_insert_line(f"✓ {agent_name} finished", "success")
                self.safe_insert_blank()

                results.append((agent_name, agent_answer))

            self.safe_insert_section("Final Answer")

            for agent_name, agent_answer in results:
                self.safe_insert_line(f"{agent_name} Result", "agent")
                self.safe_insert_block(agent_answer)
                self.safe_insert_blank()

        except Exception as error:
            self.safe_insert_blank()
            self.safe_insert_line("Unexpected error", "error")
            self.safe_insert_line(f"{type(error).__name__}: {error}", "error")

        finally:
            self.root.after(0, self.reset_run_button)

    def safe_insert_section(self, title: str) -> None:
        self.root.after(0, self.insert_section, title)

    def safe_insert_line(self, text: str, tag: str = "body") -> None:
        self.root.after(0, self.insert_line, text, tag)

    def safe_insert_blank(self) -> None:
        self.root.after(0, self.insert_line, "", "body")

    def safe_insert_block(self, text: str) -> None:
        for raw_line in text.splitlines():
            clean_line = self.clean_markdown_line(raw_line)
            tag = self.infer_tag(clean_line)
            self.root.after(0, self.insert_line, clean_line, tag)

    def insert_section(self, title: str) -> None:
        self.output_box.configure(state="normal")
        self.output_box.insert(tk.END, "\n", "body")
        self.output_box.insert(tk.END, f"{title}\n", "section")
        self.output_box.insert(tk.END, "─" * 72 + "\n", "muted")
        self.output_box.configure(state="disabled")
        self.output_box.see(tk.END)

    def insert_line(self, text: str, tag: str = "body") -> None:
        self.output_box.configure(state="normal")
        self.output_box.insert(tk.END, text + "\n", tag)
        self.output_box.configure(state="disabled")
        self.output_box.see(tk.END)

    def clean_markdown_line(self, line: str) -> str:
        cleaned = line.strip()

        if cleaned.startswith("### "):
            cleaned = cleaned[4:]

        if cleaned.startswith("## "):
            cleaned = cleaned[3:]

        if cleaned.startswith("# "):
            cleaned = cleaned[2:]

        cleaned = cleaned.replace("**", "")
        cleaned = cleaned.replace("*", "")
        cleaned = cleaned.replace("`", "")

        return cleaned

    def infer_tag(self, line: str) -> str:
        if not line:
            return "body"

        if line.startswith("|"):
            return "table"

        if line.startswith("-"):
            return "body"

        if line.startswith("✓"):
            return "success"

        if line.endswith("Result"):
            return "agent"

        if line.startswith("Unexpected error"):
            return "error"

        important_prefixes = (
            "User request:",
            "Router decision:",
            "Selected agent",
            "Reason:",
            "Country sub-query:",
            "Weather sub-query:",
            "Time sub-query:",
            "Query:",
            "Source:",
            "Location:",
            "Time zone:",
            "Current time:",
            "Date:",
            "Weekday:",
            "UTC offset:",
        )

        if line.startswith(important_prefixes):
            return "label"

        return "body"

    def write_output(self, text: str) -> None:
        self.clear_output()
        for line in text.splitlines():
            self.insert_line(self.clean_markdown_line(line), self.infer_tag(line))

    def clear_output(self) -> None:
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", tk.END)
        self.output_box.configure(state="disabled")

    def reset_run_button(self) -> None:
        self.run_button.config(state="normal", text="Run")


def main() -> None:
    root = tk.Tk()
    MultiAgentAssistantGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()