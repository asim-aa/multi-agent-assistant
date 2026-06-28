# 🤖 Multi-Agent Assistant

A modular multi-agent AI assistant built in Python using an OpenAI-compatible Large Language Model (LLM), function calling, and specialized AI agents.

Instead of relying on a single monolithic prompt, this project demonstrates how modern agentic systems decompose a user's request into specialized tasks, delegate those tasks to domain-specific agents, retrieve live information through external APIs or tools, and combine the results into a single coherent response.

Although this project was developed using the **SupportVectors AI Cluster**, the architecture is provider-agnostic and works with any OpenAI-compatible endpoint (OpenAI, Azure OpenAI, Ollama, vLLM, Together AI, etc.) by updating the environment variables.

---

# Features

* 🧠 **LLM Router Agent** for intent classification and sub-query extraction
* 🌦️ **Weather Agent** powered by the Open-Meteo API
* 🌍 **Country Agent** powered by the World Bank Country API
* 🕒 **Time Agent** powered by Python's `zoneinfo`
* 🔧 OpenAI Function / Tool Calling
* 🤖 Multi-agent orchestration
* 📦 Modular architecture following the Single Responsibility Principle
* 🔄 Provider-agnostic OpenAI-compatible client
* 🧩 Easily extensible with additional specialized agents

---

# Example

### User Request

```text
Tell me about Japan, what is the weather in Tokyo, and what time is it there?
```

### Router Decision

```text
Intent: Multi-Agent

Country Query:
Tell me about Japan

Weather Query:
What is the weather in Tokyo, Japan?

Time Query:
What time is it in Tokyo, Japan?
```

### Execution Pipeline

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

### Result

The assistant:

* retrieves country information from the World Bank API
* retrieves live weather from Open-Meteo
* retrieves the local time using Python's time zone database
* combines all results into a single natural-language response

---

# Architecture

```text
                         User
                           │
                           ▼
                        main.py
                           │
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
    ├── main.py
    ├── router.py
    ├── prompts.py
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

The Router Agent is responsible for understanding the user's request and deciding which specialized agent(s) should handle it.

Examples:

* Weather question → Weather Agent
* Country question → Country Agent
* Time question → Time Agent
* Combined question → Multiple agents

Rather than answering the question itself, the router extracts clean sub-queries and delegates work to the appropriate agents.

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

Instead of relying solely on the model's internal knowledge, agents retrieve live information using external tools.

Current tools include:

* Open-Meteo Weather API
* World Bank Country API
* Python `zoneinfo`

This approach reduces hallucinations while ensuring responses are grounded in reliable data sources.

---

## Modular Design

The project intentionally separates responsibilities across multiple modules.

* `main.py` orchestrates the application
* `router.py` performs LLM-based routing
* `agents/` contains domain-specific reasoning
* `tools/` communicates with external services
* `prompts.py` centralizes system prompts

This architecture makes the system easier to maintain, debug, and extend as additional agents are introduced.

---

# Installation

Clone the repository.

```bash
git clone https://github.com/asim-aa/multi-agent-assistant.git
cd multi-agent-assistant
```

Create and activate a virtual environment.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

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

Run the assistant.

```bash
python -m multi_agent_assistant.main
```

---

# Technologies

* Python
* OpenAI Python SDK
* OpenAI-Compatible Chat Completions API
* Function Calling / Tool Calling
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
Router Decision:
Multi-Agent

✓ Country Agent
✓ Weather Agent
✓ Time Agent

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Final Answer

• Country information retrieved from the World Bank API
• Current weather retrieved from Open-Meteo
• Current local time retrieved using zoneinfo
• Responses combined into one final answer
```

---

# Future Improvements

* Parallel agent execution with `asyncio`
* Conversation memory
* Agent registry for plug-and-play expansion
* Streaming responses
* Docker deployment
* FastAPI or Streamlit web interface
* Router evaluation suite
* Logging and telemetry
* Additional agents (Currency, News, Travel, Public Holidays)

---

# Documentation

For a detailed walkthrough of the architecture, design decisions, implementation process, and lessons learned, see:

```text
docs/ARCHITECTURE.md
```

This document explains the reasoning behind the project, including router agents, function calling, modular architecture, prompt organization, message flow, and future scalability.

---

# License

This project is provided for educational and portfolio purposes.
