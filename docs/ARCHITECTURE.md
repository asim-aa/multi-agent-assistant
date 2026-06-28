# Architecture Notes: Multi-Agent Assistant

This document is a deeper technical and conceptual walkthrough of the Multi-Agent Assistant project.

The main `README.md` is written for a professional GitHub audience: what the project does, how to run it, and why it matters. This document is different. This file explains how the project evolved, why the files are separated the way they are, what each part is responsible for, and what I learned while building it.

The goal of this project was not just to connect two APIs. The goal was to understand how an AI assistant can be structured as a system of cooperating parts: a router, specialized agents, tools, prompts, and external services.

---

# 1. Project Overview

The Multi-Agent Assistant is a Python application that uses an LLM router to decide which specialized agent should handle a user's request.

Currently, it supports two agents:

* Weather Agent
* Country Agent

The Weather Agent retrieves live weather data using the Open-Meteo API.

The Country Agent retrieves country information using the World Bank Country API.

The key feature is that the user does not need to manually choose the agent. The user can ask a natural-language question, and the router decides where the request should go.

Example:

```text
Tell me about Japan and what is the weather in Tokyo?
```

The router detects that this is a multi-agent request. It splits the request into two cleaner sub-queries:

```text
Country query:
Tell me about Japan

Weather query:
What is the weather in Tokyo, Japan?
```

Then the Country Agent handles the country query and the Weather Agent handles the weather query. The system combines both results into one final response.

---

# 2. High-Level System Flow

The application follows this flow:

```text
User
  ↓
main.py
  ↓
router.py
  ↓
Selected agent(s)
  ↓
Agent-specific tool(s)
  ↓
External API
  ↓
Structured result
  ↓
Agent explanation
  ↓
Final combined response
```

A more detailed view:

```text
                    User
                      │
                      ▼
                  main.py
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

Each arrow matters:

* The user sends one natural-language request.
* `main.py` receives the request and controls the program loop.
* `router.py` decides which agent or agents should run.
* Each agent receives only the part of the query relevant to its domain.
* Each agent calls a tool.
* Each tool calls an external API.
* The tool returns structured data.
* The agent explains the result.
* `main.py` prints the final answer.

---

# 3. Why This Project Started as a Weather Agent

The first version of this project was a simple Weather Agent.

The goal was straightforward:

```text
User enters a city
  ↓
LLM receives the request
  ↓
LLM calls get_weather()
  ↓
Python calls Open-Meteo
  ↓
Weather result returns
  ↓
LLM explains it
```

This was useful because it introduced the core agent pattern:

```text
LLM + Tool + External API + Final Explanation
```

At this stage, there was only one domain: weather.

The first working version helped me understand that the LLM itself does not know the live weather. The LLM is not the source of truth. The tool is the source of truth.

The LLM's job is to understand the request, decide to call the tool, and explain the tool result.

That distinction became one of the most important lessons in the project.

---

# 4. Why the Project Became Multi-Agent

After the Weather Agent worked, the next question was:

What happens when the assistant can do more than one thing?

For example:

```text
What is the weather in Tokyo?
```

is a weather task.

But:

```text
Tell me about Japan.
```

is a country-information task.

And:

```text
Tell me about Japan and what is the weather in Tokyo?
```

contains both.

If the project only had one giant assistant, all the logic would get mixed together. Weather logic, country logic, API calls, prompts, routing, and formatting would all live in one place.

That would make the code difficult to debug and difficult to extend.

The multi-agent structure solves that problem.

Instead of one giant assistant, the project uses:

```text
Router Agent
  ↓
Weather Agent
  ↓
Country Agent
```

Each specialized agent focuses on one domain.

The Router Agent does not answer the user directly. It decides who should answer.

---

# 5. What a Router Agent Does

A Router Agent is like a dispatcher.

It receives the user's request and decides which expert should handle it.

It does not call the weather API.

It does not call the country API.

It does not produce the final answer.

Its job is to classify and delegate.

Examples:

```text
User:
What is the weather in Tokyo?

Router:
weather
```

```text
User:
Tell me about Japan.

Router:
country
```

```text
User:
Tell me about Japan and what is the weather in Tokyo?

Router:
multi
```

In this project, the router returns a structured decision object containing:

* route
* selected agent name
* reason
* weather sub-query
* country sub-query

Example router output:

```json
{
  "route": "multi",
  "agent_name": "Weather Agent + Country Agent",
  "reason": "User requested both country information and weather",
  "country_query": "Tell me about Japan",
  "weather_query": "What is the weather in Tokyo, Japan?"
}
```

This is better than simply returning one word because the router also cleans the input for each agent.

Instead of sending the full mixed request to both agents, each agent gets the part it needs.

That was an important fix.

---

# 6. Keyword Routing vs LLM Routing

An early version of the router used keyword matching.

Example:

```python
if "weather" in text:
    return "weather"
```

This worked for simple questions, but it was limited.

It could detect:

```text
What is the weather in Tokyo?
```

But it struggled with more flexible natural language.

It also could not reliably extract clean sub-queries.

The improved version uses an LLM Router.

The LLM Router receives the user request and returns structured JSON.

This gives the system more flexibility:

```text
Tell me about Japan and what is the weather in Tokyo?
```

becomes:

```text
route = multi
country_query = Tell me about Japan
weather_query = What is the weather in Tokyo, Japan?
```

This mirrors a common pattern in agentic systems: using an LLM to classify intent and prepare structured work for downstream components.

The keyword router is still useful as a fallback, but the LLM router is the main routing mechanism.

---

# 7. Why `main.py` Exists

`main.py` is the entry point of the application.

Before having a main file, each agent had to be run separately:

```bash
python -m multi_agent_assistant.agents.weather_agent
python -m multi_agent_assistant.agents.country_agent
```

That works for testing, but it does not feel like one assistant.

A real assistant should have one entry point:

```bash
python -m multi_agent_assistant.main
```

The purpose of `main.py` is to orchestrate the full workflow:

1. Ask the user for input.
2. Send the input to the router.
3. Display the router's decision.
4. Execute the selected agent or agents.
5. Print the final response.

`main.py` should not contain weather API logic or country API logic.

It coordinates the system, but it does not do the specialized work.

This makes the program easier to understand:

```text
main.py = application loop and orchestration
router.py = decision-making
agents/ = domain reasoning
tools/ = external API calls
```

---

# 8. Why an Agent Registry Was Added

An early version of `main.py` used explicit conditional logic:

```python
if decision.route == "weather":
    run_weather_agent(...)

elif decision.route == "country":
    run_country_agent(...)

elif decision.route == "multi":
    run both
```

This worked with two agents, but it would become messy as more agents are added.

If the project later includes:

* Currency Agent
* News Agent
* Time Zone Agent
* Travel Agent
* Book Agent

then a long chain of `if/elif` statements would become harder to maintain.

The improved version uses an agent registry:

```python
AGENTS = {
    "weather": run_weather_agent,
    "country": run_country_agent,
}
```

This creates a cleaner pattern:

```text
route key
  ↓
lookup agent function
  ↓
run selected agent
```

Now adding a new agent becomes more systematic:

1. Create the new agent file.
2. Create the new tool file.
3. Register the agent in `AGENTS`.
4. Update the router prompt to know about the new route.

This is more scalable than hardcoding every path into `main.py`.

---

# 9. Why Tools Are Separate from Agents

Tools are responsible for real-world actions.

Agents are responsible for reasoning and explanation.

This distinction matters.

The Weather Agent should not contain all the raw `requests.get(...)` logic for Open-Meteo.

The Country Agent should not contain all the raw HTTP handling for the World Bank API.

Instead, each API call lives in the `tools/` folder.

Example:

```text
Weather Agent
  ↓
get_weather()
  ↓
Open-Meteo API
```

The tool returns structured data, usually as a Python dictionary.

The agent receives that dictionary and explains it.

This separation has several advantages:

* The tool can be tested independently.
* The agent prompt can change without touching API code.
* The API implementation can change without rewriting the agent.
* Multiple agents could reuse the same tool in the future.

A tool should not be conversational.

A tool should return data.

The agent turns that data into language.

---

# 10. Why Tools Return Dictionaries

The tools in this project return dictionaries instead of full natural-language responses.

For example, a weather tool might return:

```python
{
    "searched_for": "Tokyo, Japan",
    "matched_location": {
        "name": "Tokyo",
        "state_or_region": "Tokyo",
        "country": "Japan"
    },
    "current_weather": {
        "temperature_2m": 71.1,
        "apparent_temperature": 77.1,
        "precipitation": 0.012,
        "wind_speed_10m": 3.0
    }
}
```

This is better than returning:

```text
The weather in Tokyo is 71 degrees...
```

because structured data gives the agent more flexibility.

The agent can decide:

* what to summarize
* how to format the answer
* whether to mention missing fields
* how to combine the result with another agent's response

Returning dictionaries also makes debugging easier because the raw tool output is inspectable.

---

# 11. Why Prompts Are Separate

Prompts live in `prompts.py`.

This was an intentional design decision.

At first, it is tempting to write prompts directly inside each agent file. That works for small scripts, but prompts often change more frequently than code.

Keeping prompts separate makes it easier to:

* edit instructions
* compare versions
* keep agent files cleaner
* centralize behavior definitions
* avoid mixing business logic with prompt text

The project uses different prompts for different roles:

* Weather Agent prompt
* Country Agent prompt
* Router Agent prompt

This reinforces the idea that each component has its own responsibility.

The router prompt focuses on classification and sub-query extraction.

The weather prompt focuses on weather interpretation.

The country prompt focuses on explaining country data.

---

# 12. Why Agents Should Not Call Each Other Directly

One design rule I wanted to preserve is that agents should not directly call each other.

For example, the Weather Agent should not call the Country Agent.

The Country Agent should not call the Weather Agent.

That would create a tangled system where control flow becomes difficult to follow.

Instead, `main.py` and `router.py` coordinate which agents run.

This keeps the architecture clean:

```text
Router decides.
main.py executes.
Agents specialize.
Tools retrieve.
```

Each layer has a clear responsibility.

If agents start calling other agents directly, the system becomes harder to debug because it is no longer obvious who is responsible for what.

---

# 13. Message Flow Through the System

A simplified message flow looks like this:

```text
User input:
Tell me about Japan and what is the weather in Tokyo?
```

`main.py` sends this to the router.

The router returns:

```text
route = multi
country_query = Tell me about Japan
weather_query = What is the weather in Tokyo, Japan?
```

`main.py` sees that this is a multi-agent request.

It runs:

```text
Country Agent with:
Tell me about Japan
```

and:

```text
Weather Agent with:
What is the weather in Tokyo, Japan?
```

Each agent creates messages for the LLM.

The LLM may call a tool.

The tool returns data.

The agent explains the data.

`main.py` combines the two agent responses.

This entire chain is visible in the terminal through the decision pipeline:

```text
Decision Pipeline
User request: Tell me about Japan and what is the weather in Tokyo?
Router decision: multi
Selected agent(s): Weather Agent + Country Agent
Country sub-query: Tell me about Japan
Weather sub-query: What is the weather in Tokyo, Japan?
```

This visible trace makes the system easier to understand and debug.

---

# 14. OpenAI-Compatible Client Design

The project uses the OpenAI Python SDK, but it does not have to use OpenAI's servers.

The client is configured with:

```python
client = OpenAI(
    base_url=os.getenv("LLM_API_BASE"),
    api_key=os.getenv("LLM_API_KEY"),
)
```

This means the backend can be swapped by changing environment variables.

Examples:

```env
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=your_openai_key
LLM_MODEL=gpt-4o-mini
```

or:

```env
LLM_API_BASE=http://10.0.10.51:8000/v1
LLM_API_KEY=dummy-key
LLM_MODEL=openai/gpt-oss-20b
```

The first could point to OpenAI.

The second could point to a local or private OpenAI-compatible endpoint such as a vLLM server or SupportVectors cluster.

This makes the project provider-agnostic.

The code does not need to care where the model is hosted as long as the endpoint follows the same chat completions interface.

---

# 15. Development Story

This project evolved in stages.

## Version 1: Single Weather Agent

The first version only handled weather.

It proved that a model could call a Python function, which then called a real external API.

The key lesson was:

```text
The LLM explains.
The tool retrieves.
```

## Version 2: Modular Weather Agent

The weather project was split into multiple files:

```text
weather_agent.py
weather_tools.py
prompts.py
```

This made the code much easier to reason about.

The agent controlled the workflow.

The tool handled the API.

The prompt controlled the behavior.

## Version 3: Multi-Agent Folder Structure

The project was reorganized into:

```text
agents/
tools/
router.py
main.py
prompts.py
```

This made the architecture ready for multiple agents.

## Version 4: Country Agent

A second agent was added using the World Bank API.

This gave the router two real specialists to choose between.

At this point, the system was no longer just a weather bot. It became a small multi-agent assistant.

## Version 5: Keyword Router

A simple router used keyword matching to choose between weather and country tasks.

This worked but was too rigid.

## Version 6: LLM Router

The keyword router was upgraded into an LLM router.

The LLM router could detect multi-agent requests and produce clean sub-queries.

This made the system feel much more intelligent.

## Version 7: Visible Decision Pipeline

The terminal UI was improved to show:

* user request
* router decision
* selected agents
* generated sub-queries
* agent execution

This made the internal workflow understandable to the user.

## Version 8: Agent Registry

The main program was refactored to use an agent registry.

This made the system easier to extend because new agents can be registered without rewriting the entire control flow.

---

# 16. Problems Encountered

## API Reliability

Not every free API behaved the way I expected.

The original idea was to add a Stock Agent using a free stock price API. That turned out to be more complicated because many stock APIs require keys, enforce strict rate limits, or reject unauthenticated requests.

This taught me an important lesson:

```text
Agent architecture and API logistics are separate problems.
```

The architecture was working, but the data provider was not reliable enough for a beginner-friendly no-key demo.

I switched to the World Bank Country API because it was simpler and better suited for learning router-agent design.

## Location Ambiguity

Weather APIs can struggle with ambiguous locations.

For example:

```text
Dublin
```

could refer to Dublin, Ireland or Dublin, California.

The weather tool needed better location normalization and alias handling.

This showed me that tools often need preprocessing logic before calling an external API.

The LLM can help generate cleaner queries, but the tool still needs defensive code.

## Prompt Output Control

The router needed to return valid JSON.

That required a strict router prompt.

If the router returned markdown or extra prose, the program would fail to parse the response.

This taught me that when LLMs are used inside software systems, output formatting matters.

The model is not just chatting. It is producing structured data that downstream code depends on.

---

# 17. Lessons Learned

The biggest lesson from this project is that an AI agent is not just an LLM.

An agentic system is a composition of parts:

```text
LLM
+
tools
+
control flow
+
state/messages
+
external data
+
routing
```

The LLM is only one piece.

The architecture around the LLM is what makes the system reliable and extensible.

I also learned that modularity matters early. Even when a project seems small, separating responsibilities makes it much easier to grow.

The difference between a toy chatbot and a more serious agent project is not always the number of features. It is often the structure.

A simple project with a clean router, tools, agents, prompts, and execution flow can teach more than a larger project with everything inside one file.

---

# 18. How I Would Improve This Further

## Add More Agents

Possible additions:

* Currency Agent
* Time Zone Agent
* News Agent
* Book Search Agent
* Travel Agent

Each new agent would follow the same pattern:

```text
agent file
tool file
prompt
router update
registry update
```

## Add Async Execution

Currently, multiple agents run sequentially.

For a multi-agent request, the Country Agent runs first, then the Weather Agent runs.

In the future, these could run in parallel using `asyncio`.

That would make multi-agent responses faster.

## Add Logging

A logging layer would make it easier to inspect:

* router decisions
* tool calls
* API responses
* errors
* execution time

## Add Evaluation

The router could be tested with a dataset of example user inputs.

Example:

```text
"What is the weather in Tokyo?" → weather
"Tell me about Iraq" → country
"Tell me about Japan and the weather in Tokyo" → multi
```

This would help measure routing accuracy.

## Add a Web UI

A Streamlit or FastAPI interface would make the project easier to demo visually.

The terminal version is useful for development, but a web UI would be stronger for presentation.

---

# 19. Final Reflection

This project started as a simple weather script.

It became a way to understand the deeper architecture behind AI agents.

The most important shift was moving from thinking:

```text
How do I make one chatbot answer everything?
```

to thinking:

```text
How do I design a system where specialized components cooperate?
```

That shift changed how I think about building AI applications.

A good agent system is not just about prompting a model well. It is about designing clear boundaries:

* the router decides
* the agent reasons
* the tool retrieves
* the external API provides facts
* the main program orchestrates

Once those boundaries are clear, the project becomes easier to extend, easier to debug, and easier to explain.
