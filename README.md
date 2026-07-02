# 🤖 Multi-Agent Assistant

A modular multi-agent AI assistant built in Python using an OpenAI-compatible Large Language Model (LLM), function calling, and specialized AI agents.

Instead of relying on one monolithic prompt, this project demonstrates how an agentic system can decompose a user's request into specialized tasks, route those tasks to domain-specific agents, retrieve live information through tools, and combine the results into one coherent response.

The assistant currently supports three specialized agents:

* 🌦️ Weather Agent
* 🌍 Country Agent
* 🕒 Time Agent

It can be used through either a terminal interface or a polished Tkinter desktop GUI.

Although this project was developed using the **SupportVectors AI Cluster**, the architecture is provider-agnostic and works with any OpenAI-compatible endpoint, including OpenAI, Azure OpenAI, Ollama, vLLM, Together AI, and similar services.

## Architecture Overview

![AI Agents Glossary ADK Pipeline](docs/architecture.png)
---

# Features

* 🧠 **LLM Router Agent** for intent classification and sub-query extraction
* 🌦️ **Weather Agent** powered by the Open-Meteo API
* 🌍 **Country Agent** powered by the World Bank Country API
* 🕒 **Time Agent** powered by Python's `zoneinfo`
* 🖥️ **Tkinter Desktop GUI** for interacting with the assistant outside the terminal
* 🔧 OpenAI Function / Tool Calling
* 🤖 Multi-agent orchestration
* 🧩 Agent registry for cleaner plug-and-play expansion
* 📦 Modular architecture following the Single Responsibility Principle
* 🔄 Provider-agnostic OpenAI-compatible client
* 🗺️ Improved location normalization for ambiguous names such as `Bangalore` → `Bengaluru`
* 🌦️ Weather-code descriptions that translate raw Open-Meteo codes into readable conditions such as `3 → Overcast`

---

# Example

## User Request

```text
Tell me about Japan, what is the weather in Tokyo, and what time is it there?
```

## Router Decision

```text
Intent: Multi-Agent

Country Query:
Tell me about Japan

Weather Query:
What is the weather in Tokyo, Japan?

Time Query:
What time is it in Tokyo, Japan?
```

## Execution Pipeline

```text
                User
                  │
                  ▼
           LLM Router Agent
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
 Country      Weather       Time
  Agent         Agent        Agent
      │           │           │
      ▼           ▼           ▼
 World Bank   Open-Meteo    zoneinfo
      └───────────┼───────────┘
                  ▼
          Combined Response
```

## Result

The assistant:

* retrieves country information from the World Bank API
* retrieves live weather from Open-Meteo
* translates weather condition codes into readable descriptions
* retrieves the local time using Python's time zone database
* combines all results into a single natural-language response

---

# Interfaces

The project supports two ways to interact with the assistant.

## Terminal Interface

```bash
python -m multi_agent_assistant.main
```

This runs the assistant directly in the terminal and displays the routing pipeline, selected agents, sub-queries, and final answer.

## Desktop GUI

```bash
python -m multi_agent_assistant.main_gui
```

This launches a Tkinter desktop window where users can enter prompts and view a styled decision pipeline and final response.

The GUI uses the same backend architecture as the terminal version. It does not duplicate agent logic. It is simply another interface layer on top of the router, agents, and tools.

---

# Architecture

```text
                         User
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
       Terminal App                  Desktop GUI
        main.py                      main_gui.py
             │                           │
             └─────────────┬─────────────┘
                           ▼
                    LLM Router Agent
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
 Country Agent      Weather Agent       Time Agent
        │                  │                  │
        ▼                  ▼                  ▼
 World Bank API      Open-Meteo API      zoneinfo
        └──────────────────┼──────────────────┘
                           ▼
                  Combined Response
```

---

# Project Structure

```text
multi-agent-assistant/

├── README.md
├── requirements.txt
├── .env.example
│
├── docs/
│   └── ARCHITECTURE.md
│
└── multi_agent_assistant/
    ├── main.py              # Terminal entry point
    ├── main_gui.py          # Tkinter desktop GUI entry point
    ├── router.py            # LLM router and task decomposition
    ├── prompts.py           # Centralized system prompts
    │
    ├── agents/
    │   ├── weather_agent.py
    │   ├── country_agent.py
    │   └── time_agent.py
    │
    └── tools/
        ├── weather_tools.py
        ├── country_tools.py
        └── time_tools.py
```

---

# Design Highlights

## LLM Router Agent

The Router Agent is responsible for understanding the user's request and deciding which specialized agent or agents should handle it.

Examples:

* Weather question → Weather Agent
* Country question → Country Agent
* Time question → Time Agent
* Combined question → Multiple agents

Rather than answering the question itself, the router extracts clean sub-queries and delegates work to the appropriate agents.

Example:

```json
{
  "route": "multi",
  "agent_name": "Weather Agent + Country Agent + Time Agent",
  "reason": "User requested country information, weather, and current time.",
  "country_query": "Tell me about Japan",
  "weather_query": "What is the weather in Tokyo, Japan?",
  "time_query": "What time is it in Tokyo, Japan?"
}
```

---

## Specialized Agents

Each agent focuses on a single domain.

Current agents include:

* 🌦️ Weather Agent
* 🌍 Country Agent
* 🕒 Time Agent

Each agent:

* reasons about its own domain
* decides when to invoke tools
* interprets structured tool responses
* generates a natural-language explanation

Agents do not communicate directly with one another. Coordination happens through the router and application orchestrator.

---

## Tool Calling

Instead of relying only on the model's internal knowledge, agents retrieve information using tools.

Current tools include:

* Open-Meteo Weather API
* World Bank Country API
* Python `zoneinfo`

This approach reduces hallucinations because live or factual information comes from tools rather than from the model's memory.

The Weather Tool also normalizes ambiguous city names and adds readable weather descriptions. For example:

```text
Bangalore, India → Bengaluru, Karnataka, India
weather_code 3 → Overcast
```

---

## Agent Registry

The project uses an agent registry instead of a long chain of `if/elif` statements.

```python
AGENTS = {
    "weather": run_weather_agent,
    "country": run_country_agent,
    "time": run_time_agent,
}
```

This makes the system easier to extend. Adding a new agent follows a predictable pattern:

1. Create the tool.
2. Create the specialized agent.
3. Register the agent.
4. Teach the router about the new route.

---

## Modular Design

The project intentionally separates responsibilities across multiple modules.

* `main.py` handles terminal orchestration.
* `main_gui.py` handles the desktop GUI.
* `router.py` performs LLM-based routing.
* `agents/` contains domain-specific reasoning.
* `tools/` communicates with external services or local capabilities.
* `prompts.py` centralizes system prompts.

This architecture makes the system easier to maintain, debug, and extend as additional agents are introduced.

---

# Installation

Clone the repository.

```bash
git clone https://github.com/asim-aa/multi-agent-assistant.git
cd multi-agent-assistant
```

Create and activate a virtual environment.

## macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

Create a `.env` file using `.env.example`.

Example:

```env
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=your_api_key
LLM_MODEL=gpt-4o-mini
```

Or use any OpenAI-compatible endpoint.

Example for a private/local OpenAI-compatible endpoint:

```env
LLM_API_BASE=http://your-openai-compatible-endpoint/v1
LLM_API_KEY=dummy-key
LLM_MODEL=your-model-name
```

---

# Usage

## Run the Terminal Version

```bash
python -m multi_agent_assistant.main
```

## Run the Desktop GUI Version

```bash
python -m multi_agent_assistant.main_gui
```

Example prompt:

```text
Tell me about India, what is the weather in Bangalore, and what is the current time there?
```

The assistant should route the request to:

* Country Agent for India
* Weather Agent for Bengaluru/Bangalore weather
* Time Agent for India Standard Time

---

# Technologies

* Python
* OpenAI Python SDK
* OpenAI-Compatible Chat Completions API
* Function Calling / Tool Calling
* Tkinter
* Requests
* Python-dotenv
* Open-Meteo API
* World Bank Country API
* Python `zoneinfo`

---

# Example Session

```text
Ask:
Tell me about Japan, what is the weather in Tokyo, and what time is it there?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Decision Pipeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Router decision: multi
Selected agent(s): Weather Agent + Country Agent + Time Agent
Country sub-query: Tell me about Japan
Weather sub-query: What is the weather in Tokyo, Japan?
Time sub-query: What time is it in Tokyo, Japan?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Executing Agents
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Country Agent running
✓ Weather Agent running
✓ Time Agent running

Final Answer:

Country Agent Result:
Country information retrieved from the World Bank API.

Weather Agent Result:
Current weather retrieved from Open-Meteo with readable weather-code descriptions.

Time Agent Result:
Current local time retrieved using Python zoneinfo.
```

---

# Future Improvements

* Parallel agent execution with `asyncio`
* Conversation memory
* Streaming responses
* Docker deployment
* FastAPI or Streamlit web interface
* Router evaluation suite
* Logging and telemetry
* Additional agents such as Currency, News, Travel, and Public Holidays

---

# Documentation

For a detailed walkthrough of the architecture, design decisions, implementation process, and lessons learned, see:

```text
docs/ARCHITECTURE.md
```

This document explains the reasoning behind the project, including router agents, function calling, modular architecture, prompt organization, message flow, tool design, and future scalability.

---

# License

This project is provided for educational and portfolio purposes.
