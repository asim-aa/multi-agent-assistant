# 🤖 Multi-Agent Assistant

A practical multi-agent AI assistant built in Python using an OpenAI-compatible Large Language Model (LLM), function calling, external tools, parallel execution, output validation, and a desktop GUI.

Instead of relying on one monolithic prompt, this project demonstrates how an agentic application can decompose a user's request into specialized tasks, route those tasks to domain-specific agents, retrieve live information from external APIs or local tools, validate the outputs, and combine the results into one coherent response.

The assistant currently supports three specialized agents:

* 🌦️ **Weather Agent**
* 🌍 **Country Agent**
* 🕒 **Time Agent**

It can be used through either a terminal interface or a Tkinter desktop GUI.

Although this project was developed using the **SupportVectors AI Cluster**, the architecture is provider-agnostic and works with any OpenAI-compatible endpoint, including OpenAI, Azure OpenAI, Ollama, vLLM, Together AI, and similar services.

---

## Architecture Overview

![Multi-Agent Assistant Architecture](docs/architecture.png)

---

# Features

* 🧠 **LLM Router Agent** for intent classification and sub-query extraction
* 🌦️ **Weather Agent** powered by the Open-Meteo API
* 🌍 **Country Agent** powered by the World Bank Country API
* 🕒 **Time Agent** powered by Python's `zoneinfo`
* ⚡ **Parallel agent execution** for independent multi-agent requests
* ✅ **Validation layer** that checks agent outputs before final response generation
* 🖥️ **Tkinter Desktop GUI** for interacting with the assistant outside the terminal
* 🔧 OpenAI Function / Tool Calling
* 🤖 Multi-agent orchestration
* 🧩 Agent registry for cleaner plug-and-play expansion
* 📦 Modular architecture following the Single Responsibility Principle
* 🔄 Provider-agnostic OpenAI-compatible client
* 🗺️ Improved location disambiguation using aliases, country matching, state/region matching, and population scoring
* 🌦️ Weather-code descriptions that translate raw Open-Meteo codes into readable conditions such as `3 → Overcast`
* 🧪 Unit tests with `pytest`

---

# Example

## User Request

```text
Tell me about India, what is the weather in Bangalore, and what is the current time there?
```

## Router Decision

```text
Intent: Multi-Agent

Country Query:
Tell me about India

Weather Query:
What is the weather in Bangalore, India?

Time Query:
What time is it in Bangalore, India?
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
           Validation Layer
                  │
                  ▼
          Combined Response
```

## Result

The assistant:

* retrieves country information from the World Bank API
* retrieves live weather from Open-Meteo
* normalizes ambiguous city names such as `Bangalore` → `Bengaluru`
* translates weather condition codes into readable descriptions
* retrieves the local time using Python's time zone database
* validates agent outputs before producing the final response
* combines all results into a single natural-language answer

---

# Interfaces

The project supports two ways to interact with the assistant.

## Terminal Interface

```bash
python -m multi_agent_assistant.main
```

The terminal version displays the router decision, selected agents, sub-queries, parallel execution status, validation result, and final answer.

## Desktop GUI

```bash
python -m multi_agent_assistant.main_gui
```

The GUI launches a Tkinter desktop window where users can enter prompts and view a styled decision pipeline and final response.

The GUI uses the same backend architecture as the terminal version. It does not duplicate agent logic. It is an interface layer on top of the router, agents, tools, and orchestration code.

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
                 Parallel Execution
                           │
                           ▼
                  Validation Layer
                           │
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
│   ├── ARCHITECTURE.md
│   └── architecture.png
│
├── tests/
│   ├── test_weather_tools.py
│   ├── test_time_tools.py
│   └── test_validator.py
│
└── multi_agent_assistant/
    ├── main.py              # Terminal entry point and orchestration
    ├── main_gui.py          # Tkinter desktop GUI entry point
    ├── router.py            # LLM router and task decomposition
    ├── prompts.py           # Centralized system prompts
    ├── validators.py        # Output validation layer
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

Example router output:

```json
{
  "route": "multi",
  "agent_name": "Weather Agent + Country Agent + Time Agent",
  "reason": "User requested country information, weather, and current time.",
  "country_query": "Tell me about India",
  "weather_query": "What is the weather in Bangalore, India?",
  "time_query": "What time is it in Bangalore, India?"
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

Instead of relying only on the model's internal knowledge, agents retrieve information using external APIs or local tools.

Current tools include:

* Open-Meteo Weather API
* World Bank Country API
* Python `zoneinfo`

This reduces hallucinations because live or factual information comes from tools rather than from the model's memory.

The Weather Tool also normalizes ambiguous city names and adds readable weather descriptions. For example:

```text
Bangalore, India → Bengaluru, Karnataka, India
weather_code 3 → Overcast
```

---

## Parallel Agent Execution

When a request requires multiple agents, the application runs independent agent tasks in parallel using `ThreadPoolExecutor`.

For example, this user request:

```text
Tell me about India, what is the weather in Bangalore, and what is the current time there?
```

can be decomposed into three independent tasks:

```text
Country Agent → India country information
Weather Agent → Bangalore/Bengaluru weather
Time Agent → Bangalore/India local time
```

Because these tasks do not depend on each other, they can run concurrently instead of sequentially.

This improves the architecture from:

```text
Country Agent → Weather Agent → Time Agent
```

to:

```text
              ┌→ Country Agent
Router Agent ─┼→ Weather Agent
              └→ Time Agent
```

---

## Validation Layer

After the agents complete, their outputs pass through a lightweight validation layer before the final answer is printed.

The validation layer checks for issues such as:

* empty agent responses
* tool failure messages
* missing weather details
* missing country details
* missing time-zone details
* unknown weather codes or incomplete results

This creates a stronger pipeline:

```text
Router → Parallel Agents → Validation Layer → Final Answer
```

The validation layer is intentionally lightweight and deterministic. It is not an adversarial reviewer or revision loop; this project focuses on practical tool orchestration rather than content critique.

---

## Location Disambiguation

The Weather Tool includes improved location handling for ambiguous city names.

It combines:

* common aliases
* city matching
* country matching
* state/region matching
* population-based scoring

This allows the assistant to better handle cases such as:

```text
Bangalore → Bengaluru, Karnataka, India
Dublin, CA → Dublin, California, United States
Tokyo → Tokyo, Tokyo, Japan
```

The alias dictionary is used as a small normalization layer, while the scoring logic handles more general geocoding disambiguation.

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
* `validators.py` checks agent outputs before final response generation.
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

# Testing

Run the test suite with:

```bash
python -m pytest -q
```

The tests cover:

* weather-code parsing
* location normalization
* country and state normalization
* location scoring and disambiguation
* validation-layer behavior
* time-tool behavior

Example successful output:

```text
22 passed
```

---

# Technologies

* Python
* OpenAI Python SDK
* OpenAI-Compatible Chat Completions API
* Function Calling / Tool Calling
* Tkinter
* Requests
* Python-dotenv
* Pytest
* Open-Meteo API
* World Bank Country API
* Python `zoneinfo`
* `ThreadPoolExecutor`

---

# Example Session

```text
Ask:
Tell me about India, what is the weather in Bangalore, and what is the current time there?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Decision Pipeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Router decision: multi
Selected agent(s): Weather Agent + Country Agent + Time Agent
Country sub-query: Tell me about India
Weather sub-query: What is the weather in Bangalore, India?
Time sub-query: What time is it in Bangalore, India?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Executing Agents in Parallel
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Country Agent started
✓ Weather Agent started
✓ Time Agent started

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validation Layer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ All agent outputs passed validation.

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

* Conversation memory
* Streaming responses
* Docker deployment
* FastAPI or Streamlit web interface
* Router evaluation suite
* Logging and telemetry
* Async-native implementation using `asyncio`
* Additional agents such as Currency, News, Travel, and Public Holidays

---

# Documentation

For a detailed walkthrough of the architecture, design decisions, implementation process, and lessons learned, see:

```text
docs/ARCHITECTURE.md
```

This document explains the reasoning behind the project, including router agents, function calling, modular architecture, prompt organization, message flow, tool design, validation, parallel execution, and future scalability.

---

# License

This project is provided for educational and portfolio purposes.
