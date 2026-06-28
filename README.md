# 🤖 Multi-Agent Assistant with LLM Routing

A modular AI agent framework built in Python using an OpenAI-compatible LLM endpoint, tool calling, and specialized agents. The assistant uses an **LLM Router Agent** to analyze a user's request, determine intent, delegate work to the appropriate specialized agent(s), execute external API calls, and combine the results into a single response.

Although this project was developed using the SupportVectors AI Cluster, the architecture is **provider-agnostic**. Any OpenAI-compatible API (OpenAI, Azure OpenAI, Ollama, vLLM, Together AI, etc.) can be substituted by changing the environment variables.

---

# Demo

### Example Request

```
Tell me about Japan and what is the weather in Tokyo?
```

### Router Decision

```
Intent: Multi-Agent

Country Query:
Tell me about Japan

Weather Query:
What is the weather in Tokyo, Japan
```

### Agents Executed

* Country Agent
* Weather Agent

### Final Response

* Country information retrieved from the World Bank API
* Current weather retrieved from Open-Meteo
* Combined into a single natural-language response

---

# Motivation

When I first began learning AI agents, my initial instinct was to place everything inside one large Python file.

That quickly became difficult to maintain.

As more tools, APIs, prompts, and reasoning logic were added, the code became tightly coupled and increasingly difficult to extend.

The goal of this project was to learn how modern AI agent systems are actually organized:

* Separate reasoning from execution.
* Separate prompts from code.
* Separate API logic from agent logic.
* Route requests instead of creating one giant assistant.

The final result is a modular multi-agent architecture that can easily grow from two agents to many specialized agents.

---

# What I Learned

This project fundamentally changed how I think about AI agents.

Instead of viewing an AI assistant as one intelligent program, I now think of it as a collection of specialized components working together.

I learned that an LLM should not necessarily perform every task itself.

Instead, its strengths are:

* understanding natural language
* reasoning
* planning
* deciding which tools to use
* deciding which specialized agent should solve a problem

Actual data retrieval should usually be delegated to tools.

This separation makes the system significantly easier to maintain, extend, and debug.

---

# High-Level Architecture

```
                    User
                      │
                      ▼
              Multi-Agent UI
                      │
                      ▼
               LLM Router Agent
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
 Country Agent                Weather Agent
        │                           │
        ▼                           ▼
 World Bank API              Open-Meteo API
        └─────────────┬─────────────┘
                      ▼
              Combined Response
```

---

# Architecture Philosophy

This project intentionally follows the **Single Responsibility Principle**.

Each file has one primary responsibility.

Rather than creating one enormous script, responsibilities are divided into independent components that can evolve separately.

This mirrors how production AI systems are commonly organized.

---

# Folder Structure

```
multi_agent_assistant/

│
├── main.py
│
├── router.py
│
├── prompts.py
│
├── agents/
│   ├── weather_agent.py
│   └── country_agent.py
│
└── tools/
    ├── weather_tools.py
    └── country_tools.py
```

---

# File Responsibilities

## main.py

The application's entry point.

Responsibilities:

* receives user input
* calls the Router Agent
* displays the routing pipeline
* executes selected agents
* combines final responses

The main program should never contain API logic.

It simply orchestrates the workflow.

---

## router.py

The Router Agent.

This file contains its own LLM.

Its job is **not** to answer the user's question.

Instead, it decides:

* Which agent should solve the problem?
* Is this a multi-agent request?
* What clean sub-queries should each agent receive?

Example:

User:

```
Tell me about Japan and what is the weather in Tokyo?
```

Router Output:

```
{
    "route":"multi",

    "country_query":
        "Tell me about Japan",

    "weather_query":
        "What is the weather in Tokyo, Japan"
}
```

The router behaves like a project manager.

It never performs the work itself.

---

## prompts.py

All system prompts live here.

Separating prompts from code provides several advantages.

It allows prompt engineering without modifying application logic.

It also makes prompts easier to compare, test, and iterate on.

Instead of searching through Python code, every instruction to the LLM exists in one location.

---

## agents/

Each file represents one specialized AI agent.

Examples:

```
Weather Agent

Country Agent
```

An agent is responsible for:

* reasoning about one domain
* deciding when to call tools
* interpreting tool results
* producing a user-friendly explanation

Agents should not know about other agents.

That responsibility belongs to the router.

---

## tools/

Tools perform the actual work.

Examples:

```
Weather API

World Bank API
```

Tools contain zero reasoning.

Their responsibilities are simply:

Input

↓

External API

↓

Raw structured data

They should return dictionaries or structured objects rather than conversational responses.

This makes them reusable by any agent.

---

# Why Separate Agents and Tools?

This separation was one of the biggest architectural lessons from the project.

The LLM is excellent at reasoning.

External APIs are excellent at retrieving information.

Those are different responsibilities.

Instead of asking an LLM to invent weather or country information, the LLM simply decides when to call a tool.

The tool retrieves the facts.

The LLM explains those facts.

This keeps hallucinations low while improving reliability.

---

# What is a Router Agent?

A Router Agent is an LLM whose only responsibility is deciding where work should go.

Instead of answering questions, it performs classification.

For example:

User:

```
Tell me about Japan
```

↓

Router

↓

```
Country Agent
```

---

User:

```
Weather in Tokyo
```

↓

Router

↓

```
Weather Agent
```

---

User:

```
Tell me about Japan and what is the weather in Tokyo?
```

↓

Router

↓

```
Country Agent

Weather Agent
```

The router delegates work instead of solving the problem itself.

---

# Tool Calling

Each specialized agent has access to one or more tools.

For example:

```
Weather Agent

↓

get_weather()

↓

Open-Meteo API
```

The agent decides whether a tool should be called.

If necessary:

* the model generates tool arguments
* Python executes the tool
* the tool returns structured JSON
* the model explains the result

This demonstrates modern function-calling workflows used by many production LLM systems.

---

# Execution Flow

```
User

↓

LLM Router

↓

Intent Classification

↓

Sub-query Extraction

↓

Selected Agent(s)

↓

Tool Calls

↓

External APIs

↓

Structured Data

↓

LLM Explanation

↓

Combined Response
```

---

# Design Decisions

## Why use multiple agents?

Instead of one massive prompt handling every task, each agent specializes in one domain.

Benefits include:

* cleaner prompts
* easier debugging
* easier testing
* better scalability
* easier maintenance

---

## Why use an LLM Router?

Initially, routing was implemented using keyword matching.

Example:

```
if "weather" in text:
```

While useful for learning, production systems increasingly use an LLM to classify intent.

The router now:

* detects user intent
* extracts clean sub-queries
* supports multi-agent execution
* scales naturally as new agents are added

---

## Why OpenAI-Compatible APIs?

The project intentionally avoids vendor lock-in.

Only environment variables need to change.

Example:

```
SupportVectors

↓

OpenAI

↓

Azure OpenAI

↓

Ollama

↓

vLLM
```

The application code remains essentially unchanged.

---

# Technologies Used

* Python
* OpenAI Python SDK
* OpenAI-Compatible Chat Completions API
* Tool Calling / Function Calling
* Open-Meteo API
* World Bank Country API
* Requests
* dotenv

---

# Installation

Clone the repository.

```
git clone <repository>
```

Create a virtual environment.

```
python -m venv .venv
```

Activate it.

Mac/Linux

```
source .venv/bin/activate
```

Install dependencies.

```
pip install -r requirements.txt
```

Create a `.env` file.

```
LLM_API_BASE=...
LLM_API_KEY=...
LLM_MODEL=...
```

Run:

```
python -m multi_agent_assistant.main
```

---

# Example Session

```
Ask:

Tell me about Japan and what is the weather in Tokyo?
```

```
Router

↓

Intent:
Multi-Agent
```

```
Country Agent

↓

World Bank API
```

```
Weather Agent

↓

Open-Meteo API
```

```
Combined Answer
```

---

# Screenshots / Demo

Include:

* Router decision pipeline
* Multi-agent execution
* Tool calling
* Final combined answer

An animated GIF of the routing process is recommended.

---

# Future Improvements

* Add Currency Agent
* Add Time Zone Agent
* Add News Agent
* Add Travel Agent
* Parallel agent execution using asyncio
* Conversation memory
* Agent registry with plug-in architecture
* Streaming responses
* Logging and telemetry
* Evaluation suite for router accuracy
* Docker deployment
* Web interface (Streamlit or FastAPI)

---

# Key Takeaways

This project taught me that modern AI systems are less about building one increasingly complex prompt and more about composing multiple simple, specialized components.

By separating routing, reasoning, tool execution, and orchestration, the system becomes easier to understand, easier to extend, and much closer to the architecture used in production AI applications.
