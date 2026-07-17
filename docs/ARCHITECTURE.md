# Architecture Notes: Multi-Agent Assistant

This document explains the architecture behind the **Multi-Agent Assistant** project: why it is split into multiple files, how the router works, how specialized agents use tools, how outputs are validated, how independent tasks run in parallel, and how the system evolved from a simple weather agent into a modular three-agent assistant.

The main `README.md` gives a fast professional overview. This document goes deeper. It is written for students, engineers, and reviewers who want to understand the design decisions behind the implementation.

---

## 1. Project Overview

The Multi-Agent Assistant is a Python application that uses an LLM-powered router to decide which specialized agent or agents should handle a user's request.

The current system supports three specialized agents:

- **Weather Agent** — retrieves live weather data using the Open-Meteo API.
- **Country Agent** — retrieves country information using the World Bank Country API.
- **Time Agent** — retrieves the current local time using Python's built-in `zoneinfo` time zone database.

The user does not manually choose an agent. They ask a normal natural-language question, and the router decides how to break it down. When a request spans multiple domains, the selected agents run concurrently, and every agent's output passes through a validation layer before the final answer is assembled.

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
                    (ThreadPoolExecutor)
                           │
                           ▼
                  Validation Layer
                           │
                           ▼
                  Combined Response
```

The architecture separates the system into clear layers:

- `main.py` / `main_gui.py` control the application loop and orchestration (terminal and Tkinter front ends share this backend — neither duplicates agent logic).
- `router.py` decides which agent or agents should run and how their sub-tasks are dispatched.
- `agents/` contains domain-specific reasoning.
- `tools/` contains the actual external capability or data retrieval logic.
- `prompts.py` centralizes system prompts and behavioral instructions.
- `validators.py` checks agent outputs before the final response is built.

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

This was one of the biggest improvements in the project. Each agent receives a focused sub-query instead of having to interpret the entire mixed request. That focused sub-query is also what makes it safe to hand `country_query`, `weather_query`, and `time_query` off to `ThreadPoolExecutor` and run them at the same time — see Section 14.

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

## 7. Why `main.py` (and `main_gui.py`) Exist

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
5. Execute the selected agents — concurrently when more than one is selected.
6. Pass their outputs through the validation layer.
7. Print the final combined answer.

`main.py` does **not** call Open-Meteo, the World Bank API, or `zoneinfo` directly. Those responsibilities belong to tools.

`main_gui.py` is a Tkinter desktop front end added later. It calls the exact same router, agents, tools, and validation layer as `main.py` — it does not reimplement any orchestration logic, it just renders the same decision pipeline and final answer in a window instead of a terminal.

The separation is:

```text
main.py / main_gui.py
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

validators.py
    ↓
Output validation before the final response
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
Execute agent (in its own thread if others are running too)
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

This is better than returning a prewritten sentence because structured data is easier to reuse, inspect, debug, and format. It is also what makes the validation layer possible — a validator can check `if not result.get("timezone")` in a way it never could against free-form prose.

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

Independence between agents is also what made it safe to later run them concurrently — see Section 14.

---

## 13. Parallel Agent Execution

Early versions of `main.py` executed selected agents one after another:

```text
Country Agent → Weather Agent → Time Agent
```

For a three-agent request, that meant paying the full latency of three sequential LLM + tool round trips even though the agents never depended on each other's output (Section 12).

Because the router already produces independent, self-contained sub-queries (`country_query`, `weather_query`, `time_query`), the agents can be dispatched to a `ThreadPoolExecutor` and run concurrently instead:

```text
              ┌→ Country Agent
Router Agent ─┼→ Weather Agent
              └→ Time Agent
```

`main.py` submits each selected agent as a separate task, waits for all of them to complete, and collects the results in the order the router selected them — not the order they happen to finish in, so the final answer stays deterministic regardless of which API responds first. Single-agent requests skip the thread pool entirely, since there's nothing to parallelize.

---

## 14. Validation Layer

Running agents concurrently introduced a new failure mode that didn't matter as much when everything ran sequentially and could be inspected one step at a time: it became easier for one agent's tool call to silently fail or return a partial result without it being obvious in the combined output.

To catch that, every agent's output now passes through a lightweight, deterministic validation layer before `main.py` builds the final answer:

```text
Router → Parallel Agents → Validation Layer → Final Answer
```

The validator checks for:

- empty agent responses
- tool failure messages
- missing weather details
- missing country details
- missing time-zone details
- unknown weather codes or incomplete results

This layer is intentionally simple. It is not an LLM call, not an adversarial reviewer, and not a revision loop — it's a set of deterministic checks against the structured dictionaries described in Section 10. If a check fails, that failure is surfaced in the decision pipeline instead of being silently merged into the final answer. Keeping it deterministic also makes it something `pytest` can cover directly (`tests/test_validator.py`), which an LLM-based reviewer would not allow.

---

## 15. Location Disambiguation

Weather and time queries both depend on correctly identifying a location, and city names are frequently ambiguous — `Tokyo`, `Dublin`, and `Bangalore` can each refer to more than one real place, or to a name the underlying geocoder doesn't recognize directly.

The Weather Tool handles this with a small pipeline rather than a single lookup:

1. **Alias matching** — a small dictionary of common alternate names (`Bangalore` → `Bengaluru`).
2. **City / country / state-region matching** — narrows candidates using whatever location context the router's sub-query included (e.g. `Dublin, CA` vs. `Dublin, Ireland`).
3. **Population-based scoring** — when multiple real candidates remain, the more populous match is preferred as the more likely intended location (Tokyo, Japan over a smaller town sharing the name).

```text
Bangalore     → Bengaluru, Karnataka, India
Dublin, CA    → Dublin, California, United States
Tokyo         → Tokyo, Tokyo, Japan
```

The alias dictionary handles the small set of well-known cases directly; the scoring logic is the general-purpose fallback for names the alias table doesn't cover. This is also why the router is prompted to produce location-qualified sub-queries (`"What is the weather in Tokyo, Japan?"` rather than just `"Tokyo"`) — the extra context from Section 5 is what the scoring step uses to disambiguate.

---

## 16. Message Flow Through the System

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
Selected Agents (submitted to ThreadPoolExecutor)
   ├── Country Agent
   ├── Weather Agent
   └── Time Agent
   ↓
Tools
   ↓
Validation Layer
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

Each specialized agent receives only its own sub-query and runs in its own thread alongside the others. Each agent calls its tool if needed, explains the result, and returns a structured response. Those responses are checked by the validation layer, and only then does `main.py` combine them into one final answer.

The terminal also displays the full decision pipeline:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Decision Pipeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Router decision: multi
Selected agent(s): Weather Agent + Country Agent + Time Agent

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
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

This makes the system easier to debug because the user can see how the request was routed, that the agents actually ran concurrently, and that validation passed, all before the final answer appears.

---

## 17. OpenAI-Compatible Client Design

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

The agents, router, prompts, tools, and validation layer remain the same regardless of which OpenAI-compatible endpoint is used.

---

## 18. Development Timeline

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

### Version 9 — Validation Layer

Added a deterministic validation layer to check every agent's structured output for missing fields or tool failures before building the final answer.

**Lesson:** Structured tool output (Section 10) isn't just useful for formatting — it's what makes automated validation possible in the first place.

---

### Version 10 — Parallel Execution

Replaced sequential agent execution with `ThreadPoolExecutor`, since the router's independent sub-queries meant the agents never needed each other's results.

**Lesson:** An architectural decision made early (agent independence, Section 12) can pay off later in a way that wasn't the original motivation for making it.

---

### Version 11 — Desktop GUI

Added `main_gui.py`, a Tkinter front end that reuses the same router, agents, tools, and validation layer as the terminal app.

**Lesson:** A clean orchestration layer means a second interface doesn't require touching the agent logic at all.

---

## 19. Challenges and Lessons Learned

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

The weather tool then performs additional location matching (Section 15) before requesting data.

This showed me that reliable tools often need preprocessing and validation in addition to API calls — the same lesson that later motivated a dedicated validation layer for agent outputs generally.

---

### Structured LLM Output

The Router Agent communicates with the rest of the application using JSON.

That means the output must follow a predictable format.

This taught me that when an LLM is part of a software system, its output is not just conversation. It is data that other parts of the program depend on.

Prompting the router to produce consistent structured output became a key part of making the application reliable.

---

### Coordinating Concurrent Agents

Once agents started running in threads instead of sequentially, a bug in one agent's tool call was harder to spot just by watching terminal output scroll by — there was no longer a clean "step 1, step 2, step 3" to eyeball.

This is what motivated the validation layer directly: rather than relying on visually inspecting sequential output, the system now checks each agent's structured result mechanically, regardless of the order threads happen to finish in.

---

## 20. Design Trade-offs

This architecture intentionally favors modularity over simplicity.

For a small project, three agents, a router, tools, prompts, a validation layer, and an agent registry may seem like more structure than necessary.

That trade-off was intentional.

Advantages:

- easier to add new agents
- cleaner separation of responsibilities
- simpler debugging
- reusable tools
- multi-agent requests no longer pay for full sequential latency
- structured, testable validation instead of only visual inspection
- clearer architecture for portfolio review

Disadvantages:

- more files
- more boilerplate
- more message passing
- concurrency adds its own class of bugs (ordering, thread safety) that a sequential version never had to consider

For a single-purpose script, this architecture would be excessive. For learning how modular AI systems work, it is exactly the kind of structure worth practicing.

---

## 21. Future Improvements

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

### Move to `asyncio`

`ThreadPoolExecutor` solved the sequential-latency problem, but an `asyncio`-native implementation would scale further and avoid thread-management overhead as more agents are added.

---

### Build a Web Interface

The terminal and Tkinter interfaces are useful for learning and debugging.

A Streamlit or FastAPI web app would make the project easier to demo visually, and would pair naturally with Docker deployment.

---

### Add Conversation Memory

Right now, each request is independent.

Conversation memory would allow the assistant to understand follow-up questions more naturally — for example resolving "what about tomorrow?" against a previous weather query.

---

### Router Evaluation Suite and Telemetry

A dedicated evaluation suite for the router's routing/JSON-extraction accuracy, plus basic logging and telemetry across agents and the validation layer, would make regressions easier to catch as the prompt set grows.

---

## 22. Final Reflection

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
- The tools retrieve information — concurrently, when more than one is needed.
- The validation layer checks the results.
- The main application (terminal or GUI) orchestrates everything.

This project taught me that good AI systems are not only about choosing the right model. They are also about designing clean, modular software that is easy to understand, extend, test, and maintain — and that architectural decisions made early (like keeping agents independent) can pay off later in ways you didn't originally plan for.
