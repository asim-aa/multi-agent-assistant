# Architecture Notes: Multi-Agent Assistant

This document explains the architecture behind the **Multi-Agent Assistant** project: why it is split into multiple files, how the router works, how specialized agents use tools, and how the system evolved from a simple weather agent into a modular three-agent assistant.

The main `README.md` gives a fast professional overview. This document goes deeper. It is written for students, engineers, and reviewers who want to understand the design decisions behind the implementation.

---

## 1. Project Overview

The Multi-Agent Assistant is a Python application that uses an LLM-powered router to decide which specialized agent or agents should handle a user's request.

The current system supports three specialized agents:

- **Weather Agent** — retrieves live weather data using the Open-Meteo API.
- **Country Agent** — retrieves country information using the World Bank Country API.
- **Time Agent** — retrieves the current local time using Python's built-in `zoneinfo` time zone database.

The user does not manually choose an agent. They ask a normal natural-language question, and the router decides how to break it down.

Example:

```text
Tell me about Japan, what is the weather in Tokyo, and what time is it there?
```

The router identifies three separate tasks and converts the request into clean sub-queries:

```text
Country query:
Tell me about Japan

Weather query:
What is the weather in Tokyo, Japan?

Time query:
What time is it in Tokyo, Japan?
```

Each specialized agent receives only the part of the request it is responsible for. The final answer is then combined into one response.

---

## 2. High-Level Architecture

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

The architecture separates the system into clear layers:

- `main.py` controls the application loop and orchestration.
- `router.py` decides which agent or agents should run.
- `agents/` contains domain-specific reasoning.
- `tools/` contains the actual external capability or data retrieval logic.
- `prompts.py` centralizes system prompts and behavioral instructions.

This structure makes the assistant easier to extend, debug, and explain.

---

## 3. What an Agent Means in This Project

In this project, an agent is not just an LLM.

An agent is a small system made of:

```text
LLM
+
system prompt
+
tool schema
+
tool execution
+
final explanation
```

The LLM understands the user's request and decides whether a tool is needed. The tool retrieves or computes the factual data. The LLM then explains the structured result in a user-friendly way.

This separation matters because the LLM is not the source of truth for live information. The tools are.

For example, the Weather Agent does not invent the current weather. It calls `get_weather()`, which retrieves real weather data from Open-Meteo. The LLM's role is to interpret and explain that result.

---

## 4. Why the Project Became Multi-Agent

The project started as a simple Weather Agent. Once that worked, the next design question was:

> What happens when the assistant can do more than one thing?

A weather request needs the Weather Agent:

```text
What is the weather in Tokyo?
```

A country-information request needs the Country Agent:

```text
Tell me about Japan.
```

A time request needs the Time Agent:

```text
What time is it in Tokyo?
```

A user can also combine all three:

```text
Tell me about Japan, what is the weather in Tokyo, and what time is it there?
```

If one giant assistant handled everything, weather logic, country logic, time logic, API calls, prompts, routing, and formatting would all be mixed together. That would make the project harder to debug and harder to extend.

The multi-agent structure solves that problem:

```text
              Router Agent
          ┌──────┼──────┐
          ▼      ▼      ▼
     Country  Weather  Time
      Agent    Agent   Agent
```

Each agent focuses on one domain. The router decides which specialists should run.

---

## 5. Router Agent

The Router Agent is the decision-maker of the system.

Its job is not to answer the user's question. Its job is to:

1. Understand the user's intent.
2. Decide which agent or agents should run.
3. Generate clean sub-queries for each selected agent.

Examples:

```text
User:
What is the weather in Tokyo?

Router:
Weather Agent
```

```text
User:
Tell me about Japan.

Router:
Country Agent
```

```text
User:
What time is it in Baghdad?

Router:
Time Agent
```

For a multi-intent request, the router can select multiple agents:

```text
User:
Tell me about Japan, what is the weather in Tokyo, and what time is it there?

Router:
Country Agent
Weather Agent
Time Agent
```

Instead of forwarding the full mixed request to every agent, the router produces structured JSON:

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

This was one of the biggest improvements in the project. Each agent receives a focused sub-query instead of having to interpret the entire mixed request.

---

## 6. Keyword Routing vs. LLM Routing

The first router used keyword matching:

```python
if "weather" in text:
    return "weather"
```

This worked for simple questions, but it had limitations. Keyword routing struggles with:

- indirect phrasing
- multiple intents in one request
- references like "there"
- clean sub-query extraction
- structured task decomposition

For example:

```text
Tell me about Japan, what is the weather in Tokyo, and what time is it there?
```

A keyword router may detect words like `weather`, `Japan`, and `time`, but it does not truly understand how to split the request into three independent tasks.

The improved router uses an LLM. The LLM returns structured JSON describing how the application should proceed:

```json
{
  "route": "multi",
  "country_query": "Tell me about Japan",
  "weather_query": "What is the weather in Tokyo, Japan?",
  "time_query": "What time is it in Tokyo, Japan?"
}
```

The rest of the program can then behave mechanically:

```text
country_query → Country Agent
weather_query → Weather Agent
time_query    → Time Agent
```

The original keyword logic remains as a fallback in case the LLM returns invalid JSON or an unexpected response. This keeps the router flexible while still improving robustness.

---

## 7. Why `main.py` Exists

`main.py` is the application's entry point.

Before adding it, each agent had to be tested separately:

```bash
python -m multi_agent_assistant.agents.weather_agent
python -m multi_agent_assistant.agents.country_agent
python -m multi_agent_assistant.agents.time_agent
```

That is useful during development, but it does not feel like one assistant.

A real assistant needs one interface:

```bash
python -m multi_agent_assistant.main
```

`main.py` is responsible for orchestration:

1. Read user input.
2. Send the request to the router.
3. Display the decision pipeline.
4. Look up the selected agents.
5. Execute each selected agent.
6. Collect the responses.
7. Print the final combined answer.

`main.py` does **not** call Open-Meteo, the World Bank API, or `zoneinfo` directly. Those responsibilities belong to tools.

The separation is:

```text
main.py
    ↓
Application orchestration

router.py
    ↓
Intent classification and task decomposition

agents/
    ↓
Domain-specific reasoning

tools/
    ↓
Capability implementation
```

---

## 8. Agent Registry

An earlier version of `main.py` used a chain of conditionals:

```python
if decision.route == "weather":
    run_weather_agent(...)

elif decision.route == "country":
    run_country_agent(...)

elif decision.route == "time":
    run_time_agent(...)
```

This works with a few agents, but it does not scale cleanly.

The project now uses an agent registry:

```python
AGENTS = {
    "weather": run_weather_agent,
    "country": run_country_agent,
    "time": run_time_agent,
}
```

The execution flow becomes:

```text
Route key
   ↓
Agent registry lookup
   ↓
Agent function
   ↓
Execute agent
```

Adding a new agent now follows a repeatable pattern:

1. Create the tool.
2. Create the specialized agent.
3. Register the agent in `AGENTS`.
4. Teach the router about the new route.

This keeps the orchestration logic stable even as new capabilities are added.

---

## 9. Why Tools Are Separate from Agents

A major architectural lesson in this project is that reasoning and execution are different responsibilities.

Agents reason. Tools execute.

The Weather Agent calls a tool:

```text
Weather Agent
      ↓
get_weather()
      ↓
Open-Meteo API
```

The Country Agent follows the same pattern:

```text
Country Agent
      ↓
get_country_info()
      ↓
World Bank Country API
```

The Time Agent also uses a tool:

```text
Time Agent
      ↓
get_current_time()
      ↓
zoneinfo + timezone lookup
```

The Time Agent is useful conceptually because it shows that a tool does not have to be an HTTP API wrapper.

A tool is an abstraction over a capability.

Sometimes that capability is an external API. Sometimes it is local Python functionality. As long as the tool accepts input and returns structured output, the agent does not need to care how the tool works internally.

---

## 10. Why Tools Return Structured Data

Tools return structured Python dictionaries instead of full English paragraphs.

For example, the Time Tool can return fields like:

```python
{
    "location": "Tokyo, Japan",
    "timezone": "Asia/Tokyo",
    "current_time": "04:10",
    "date": "2026-06-29",
    "weekday": "Monday",
    "utc_offset": "+09:00"
}
```

This is better than returning a prewritten sentence because structured data is easier to reuse, inspect, debug, and format.

The agent can decide:

- what to include
- how to explain it
- how to handle missing values
- how to format the final response

The tool retrieves facts. The agent turns those facts into language.

---

## 11. Why Prompts Are Separate

Prompts live in `prompts.py` instead of being scattered across the codebase.

This keeps prompts easier to edit, compare, and maintain.

Each component has a different job, so each component needs different instructions:

```text
Router prompt
    ↓
Intent classification and sub-query extraction

Weather prompt
    ↓
Weather tool usage and explanation

Country prompt
    ↓
Country tool usage and explanation

Time prompt
    ↓
Time tool usage and explanation
```

The larger lesson is:

> Different responsibilities deserve different prompts.

Trying to force one enormous system prompt to perform every task usually leads to more complicated instructions, more edge cases, and lower maintainability.

---

## 12. Why Agents Should Not Call Each Other Directly

The agents in this project are intentionally independent.

The Weather Agent does not call the Country Agent. The Country Agent does not call the Time Agent. The Time Agent does not call the Weather Agent.

Coordination happens through the Router Agent and `main.py`.

```text
User
   ↓
main.py
   ↓
Router Agent
   ├── Country Agent
   ├── Weather Agent
   └── Time Agent
```

This keeps the control flow easy to understand.

- The router decides what should run.
- `main.py` executes the selected agents.
- Each agent solves only its assigned task.
- Each tool retrieves or computes the needed data.

This matters because adding the Time Agent did not require rewriting the Weather Agent or Country Agent. The new capability was added by creating a new tool, creating a new agent, registering it, and updating the router.

That is the benefit of modular architecture.

---

## 13. Message Flow Through the System

Suppose the user asks:

```text
Tell me about Japan, what is the weather in Tokyo, and what time is it there?
```

The request flows through the system like this:

```text
User
   ↓
main.py
   ↓
LLM Router
   ↓
Country Agent
Weather Agent
Time Agent
   ↓
Tools
   ↓
Combined Response
```

The router first breaks the request into smaller tasks:

```text
Country query:
Tell me about Japan

Weather query:
What is the weather in Tokyo, Japan?

Time query:
What time is it in Tokyo, Japan?
```

Each specialized agent receives only its own sub-query. Each agent calls its tool if needed, explains the result, and returns a response.

Finally, `main.py` combines the agent responses into one final answer.

The terminal also displays the decision pipeline:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Decision Pipeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Router decision: multi

Country Agent
✓ Selected

Weather Agent
✓ Selected

Time Agent
✓ Selected
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

This makes the system easier to debug because the user can see how the request was routed before the final answer appears.

---

## 14. OpenAI-Compatible Client Design

One design goal was to avoid being tied to a single AI provider.

The application uses the OpenAI Python SDK, but the model can come from many different places.

The client is configured with environment variables:

```python
client = OpenAI(
    base_url=os.getenv("LLM_API_BASE"),
    api_key=os.getenv("LLM_API_KEY"),
)
```

This means the same code can connect to:

- OpenAI
- Azure OpenAI
- Ollama
- vLLM
- Together AI
- SupportVectors AI Cluster

Only the values in `.env` need to change.

This taught me an important architectural lesson:

> Good application design separates application logic from infrastructure.

The agents, router, prompts, and tools remain the same regardless of which OpenAI-compatible endpoint is used.

---

## 15. Development Timeline

This project grew gradually rather than being built all at once.

### Version 1 — Weather Agent

Built a simple Weather Agent that could call the Open-Meteo API through tool calling.

**Lesson:** The LLM explains the data, but the tool retrieves it.

---

### Version 2 — Modular Design

Split the project into separate agent, tool, and prompt files.

**Lesson:** Separating responsibilities makes the code much easier to maintain.

---

### Version 3 — Country Agent

Added a second specialized agent using the World Bank Country API.

**Lesson:** One assistant can delegate work to multiple specialists.

---

### Version 4 — Router Agent

Introduced a router to decide which agent should handle each request.

**Lesson:** Routing should be separated from domain reasoning.

---

### Version 5 — LLM Router

Replaced simple keyword matching with an LLM router that returns structured routing decisions and clean sub-queries.

**Lesson:** LLMs can be used for task decomposition, not just final answers.

---

### Version 6 — Agent Registry

Introduced an agent registry so new agents can be added without rewriting the application's control flow.

**Lesson:** Good architecture should make future expansion straightforward.

---

### Version 7 — Time Agent

Added a third specialized agent capable of retrieving the current local time for a location.

**Lesson:** Tools do not always have to call web APIs. They simply provide capabilities that agents can use.

---

### Version 8 — Decision Pipeline

Added a visible routing pipeline to the terminal so users can see how requests move through the system.

**Lesson:** Showing the execution path makes the architecture easier to understand and debug.

---

## 16. Challenges and Lessons Learned

### Choosing Reliable APIs

The original plan was to build a Stock Agent.

Although the routing architecture worked, finding a free, reliable stock API was more difficult than expected because of authentication requirements, rate limits, and changing endpoints.

Rather than forcing an unreliable dependency into the project, I replaced it with the Country Agent.

This reinforced an important lesson:

> A good architecture should not depend on one specific external service.

---

### Handling Ambiguous Locations

Weather and time queries depend on correctly identifying locations.

For example:

```text
Tokyo
```

or

```text
Dublin
```

can refer to multiple places.

To improve accuracy, the router generates cleaner sub-queries such as:

```text
What is the weather in Tokyo, Japan?
```

The weather tool then performs additional location matching before requesting data.

This showed me that reliable tools often need preprocessing and validation in addition to API calls.

---

### Structured LLM Output

The Router Agent communicates with the rest of the application using JSON.

That means the output must follow a predictable format.

This taught me that when an LLM is part of a software system, its output is not just conversation. It is data that other parts of the program depend on.

Prompting the router to produce consistent structured output became a key part of making the application reliable.

---

## 17. Design Trade-offs

This architecture intentionally favors modularity over simplicity.

For a small project, three agents, a router, tools, prompts, and an agent registry may seem like more structure than necessary.

That trade-off was intentional.

Advantages:

- easier to add new agents
- cleaner separation of responsibilities
- simpler debugging
- reusable tools
- clearer architecture for portfolio review

Disadvantages:

- more files
- more boilerplate
- more message passing
- slightly more latency for multi-agent requests

For a single-purpose script, this architecture would be excessive. For learning how modular AI systems work, it is exactly the kind of structure worth practicing.

---

## 18. Future Improvements

The project is fully functional, but there are several directions I would explore next.

### Add More Agents

Possible additions include:

- Currency Agent
- News Agent
- Public Holiday Agent
- Travel Agent
- Book Search Agent

Each new agent would follow the same pattern:

```text
Tool
   ↓
Agent
   ↓
Router update
   ↓
Agent registry
```

---

### Run Agents in Parallel

Currently, if multiple agents are selected, they execute one after another.

In the future, I would use `asyncio` so independent agents can run at the same time.

---

### Build a Web Interface

The terminal interface is useful for learning and debugging.

A Streamlit or FastAPI web app would make the project easier to demo visually.

---

### Add Conversation Memory

Right now, each request is independent.

Conversation memory would allow the assistant to understand follow-up questions more naturally.

---

## 19. Final Reflection

This project began as a simple Weather Agent.

It became an exercise in understanding how AI applications are designed as systems.

The biggest shift in my thinking was moving from:

```text
How do I build one assistant that does everything?
```

to:

```text
How do I build a system where specialized components work together?
```

That change influenced every architectural decision in the project.

Instead of creating one large assistant, I built a system where each component has a clear responsibility:

- The router decides.
- The agents reason.
- The tools retrieve information.
- The main application orchestrates everything.

This project taught me that good AI systems are not only about choosing the right model. They are also about designing clean, modular software that is easy to understand, extend, and maintain.
