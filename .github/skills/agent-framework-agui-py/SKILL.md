---
name: agent-framework-agui-py
description: Build AG-UI (Agent UI) protocol servers and clients in Python with the Microsoft Agent Framework (`agent-framework-ag-ui`). Use when hosting an `Agent` or `Workflow` as a streaming HTTP endpoint via `add_agent_framework_fastapi_endpoint`, consuming an AG-UI server with `AGUIChatClient`, wiring hybrid client-side + server-side tool calls, managing thread-scoped state and conversation continuity, returning rich tool payloads via `state_update`, or implementing the seven standard AG-UI features (chat, backend tool rendering, human-in-the-loop, generative UI, tool-based UI, shared state, predictive state updates).
license: MIT
metadata:
  author: Microsoft
  version: "1.0.0"
  package: agent-framework-ag-ui
---

# Microsoft Agent Framework — AG-UI Integration (Python)

AG-UI (Agent UI) is a protocol for streaming agent interactions over HTTP using Server-Sent Events. `agent-framework-ag-ui` lets you expose any `Agent` or `Workflow` as an AG-UI server with one call, and consume any AG-UI server through `AGUIChatClient` — including hybrid execution where some tools run on the server and others run in the client.

## Architecture

```
   ┌──────────────────────────────────────┐         ┌──────────────────────────────────────┐
   │             AG-UI Server             │   SSE   │             AG-UI Client             │
   │                                      │ ◄─────► │                                      │
   │  FastAPI + add_agent_framework_      │  HTTP   │  AGUIChatClient                      │
   │  fastapi_endpoint(app, target, "/")  │         │  ├─ direct .get_response(...)        │
   │                                      │         │  └─ wrapped: Agent(client=AGUI…)     │
   │  target ∈ {Agent, Workflow,          │         │                                      │
   │            AgentFrameworkAgent,      │         │  - streaming + non-streaming         │
   │            AgentFrameworkWorkflow}   │         │  - thread_id continuity              │
   │                                      │         │  - hybrid tool execution             │
   │  Optional: dependencies=[Depends(…)] │         │  - interrupt / resume passthrough    │
   └──────────────────┬───────────────────┘         └──────────────────┬───────────────────┘
                      │                                                │
                      ▼                                                ▼
            Server-side tools                                Client-side tools
            (executed in-process)                            (executed locally via
                                                              function-invocation mixin)
```

Both sides use the same Agent Framework primitives (`Agent`, `@tool`, `Message`, `Content`, `AgentSession`). The AG-UI layer translates between the wire protocol and those primitives.

## Installation

```bash
pip install agent-framework-ag-ui
# or
uv pip install agent-framework-ag-ui

# Server also needs FastAPI + uvicorn (transitively pulled, pin explicitly for production):
pip install fastapi uvicorn

# Examples package with seven feature demos:
pip install agent-framework-ag-ui-examples
```

The integration exports from two equivalent paths:

```python
from agent_framework.ag_ui import (
    AGUIChatClient,
    AgentFrameworkAgent,
    AgentFrameworkWorkflow,
    add_agent_framework_fastapi_endpoint,
    state_update,
)
# Or directly:
from agent_framework_ag_ui import AGUIChatClient
```

> Status: the AG-UI protocol is still evolving — pin to a known-good `agent-framework-ag-ui` version in production.

## Environment Variables

Server samples use an Azure OpenAI deployment exposed through `OpenAIChatCompletionClient`:

| Variable | Purpose |
| --- | --- |
| `AZURE_OPENAI_ENDPOINT` | `https://<resource>.openai.azure.com/` |
| `AZURE_OPENAI_MODEL` | Deployment name (e.g. `gpt-4o-mini`) |
| `AZURE_OPENAI_API_KEY` | API key, or omit and rely on `DefaultAzureCredential` (`az login`) |
| `AG_UI_API_KEY` | Optional shared secret for the `X-API-Key` dependency |
| `AGUI_SERVER_URL` | Client-side: defaults to `http://127.0.0.1:5100/` |

Any `SupportsChatGetResponse` client works (`OpenAIChatClient`, `OpenAIChatCompletionClient`, Azure AI Foundry, custom) — AG-UI does not lock the model provider.

## Core Workflow

### 1. Host an `Agent` as an AG-UI endpoint

```python
import os
from agent_framework import Agent
from agent_framework.openai import OpenAIChatCompletionClient
from agent_framework.ag_ui import add_agent_framework_fastapi_endpoint
from fastapi import FastAPI

agent = Agent(
    name="AGUIAssistant",
    instructions="You are a helpful assistant.",
    client=OpenAIChatCompletionClient(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        model=os.environ["AZURE_OPENAI_MODEL"],
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    ),
)

app = FastAPI(title="AG-UI Server")
add_agent_framework_fastapi_endpoint(app, agent, "/")

# uvicorn server:app --host 127.0.0.1 --port 5100
```

`add_agent_framework_fastapi_endpoint(app, target, path, *, dependencies=None, ...)` accepts any `SupportsAgentRun` (an `Agent` or an `AgentFrameworkAgent` wrapper) **or** a `Workflow` / `AgentFrameworkWorkflow`. It registers a streaming POST route that emits AG-UI events as SSE.

### 2. Consume an AG-UI server with `AGUIChatClient`

```python
import asyncio
import os
from typing import cast
from agent_framework import ChatResponse, ChatResponseUpdate, Message, ResponseStream
from agent_framework.ag_ui import AGUIChatClient


async def main():
    server_url = os.environ.get("AGUI_SERVER_URL", "http://127.0.0.1:5100/")
    async with AGUIChatClient(endpoint=server_url) as client:
        thread_id: str | None = None
        while True:
            message = input("\nUser (:q to quit): ")
            if message.lower() in (":q", "quit"):
                break

            metadata = {"thread_id": thread_id} if thread_id else None
            stream = client.get_response(
                [Message(role="user", contents=[message])],
                stream=True,
                options={"metadata": metadata} if metadata else None,
            )
            stream = cast(ResponseStream[ChatResponseUpdate, ChatResponse], stream)

            print("Assistant: ", end="", flush=True)
            async for update in stream:
                if not thread_id and update.additional_properties:
                    thread_id = update.additional_properties.get("thread_id")
                for content in update.contents:
                    if content.type == "text" and content.text:
                        print(content.text, end="", flush=True)
            print()


asyncio.run(main())
```

- `AGUIChatClient` is a `BaseChatClient` — it slots into any place a chat client is expected.
- Use `async with` to clean up the underlying HTTP connection automatically.
- The first streamed update carries `additional_properties["thread_id"]` — pass it back via `metadata` on subsequent calls to keep the conversation on the same server-side thread.

### 3. Host a `Workflow`

`add_agent_framework_fastapi_endpoint` accepts a built `Workflow` directly. Outputs from `ctx.yield_output(...)` are streamed back as AG-UI events:

```python
from agent_framework import WorkflowBuilder, WorkflowContext, executor
from agent_framework.ag_ui import add_agent_framework_fastapi_endpoint
from fastapi import FastAPI

@executor(id="start")
async def start(message: str, ctx: WorkflowContext) -> None:
    await ctx.yield_output(f"Workflow received: {message}")

workflow = WorkflowBuilder(start_executor=start).build()

app = FastAPI()
add_agent_framework_fastapi_endpoint(app, workflow, "/")
```

For workflows with **runtime state** (e.g. pending `ctx.request_info` interrupts, in-flight super-steps), build a fresh instance per thread with `AgentFrameworkWorkflow(workflow_factory=...)`:

```python
from agent_framework import Workflow, WorkflowBuilder
from agent_framework.ag_ui import AgentFrameworkWorkflow, add_agent_framework_fastapi_endpoint

def build_workflow_for_thread(thread_id: str) -> Workflow:
    return WorkflowBuilder(start_executor=...).build()

thread_scoped = AgentFrameworkWorkflow(
    workflow_factory=build_workflow_for_thread,
    name="my_workflow",
)
add_agent_framework_fastapi_endpoint(app, thread_scoped, "/")
```

Without a factory, all threads share one `Workflow` instance — fine for stateless graphs, but unsafe for graphs that buffer per-conversation state.

## Hybrid tool execution

The hallmark of AG-UI: client-side tools and server-side tools coexist in **one** conversation. The server LLM sees every tool definition (its own + the client's) and decides which to call; the framework routes execution to the right side.

```
Client defines:        Server defines:
  get_weather()          get_time_zone()

User: "What's the weather in SF and what time is it?"
   │
   ▼
Agent sends full history + client tool definitions to the server
   │
   ▼
Server LLM plans: get_weather('SF'), get_time_zone('SF')
   │
   ▼
Server executes get_time_zone('SF') → "Pacific Time (UTC-8)"
Server emits function-call request → get_weather('SF')
   │
   ▼
Agent's function-invocation mixin intercepts → runs get_weather locally
   │
   ▼
Result ("Sunny, 72°F") returns to server
   │
   ▼
Server LLM combines both → "It's sunny and 72°F in SF, and the timezone is PT (UTC-8)."
```

Required wiring:

| Side | Where | What |
| --- | --- | --- |
| Server | `Agent(..., tools=[server_only_tools])` | Tools the server executes. **Do not** include client tools here. |
| Client | `Agent(name=..., client=AGUIChatClient(...), tools=[client_tools])` | Tools the client executes; metadata is forwarded to the server. |

Without the `Agent` wrapper the client cannot execute client-side tools (the function-invocation middleware lives on `Agent`). Direct `AGUIChatClient.get_response(..., tools=[...])` sends tool **definitions** only — execution must happen on the server.

```python
from agent_framework import Agent, tool
from agent_framework.ag_ui import AGUIChatClient


@tool(description="Get the current weather for a location.")
def get_weather(location: str) -> str:
    weather = {"seattle": "Rainy, 55°F", "san francisco": "Foggy, 62°F"}
    return weather.get(location.lower(), f"No data for {location}")


async with AGUIChatClient(endpoint=server_url) as remote_client:
    agent = Agent(
        name="remote_assistant",
        instructions="You are a helpful assistant.",
        client=remote_client,           # remote LLM lives behind AG-UI
        tools=[get_weather],            # this tool runs locally
    )
    session = agent.create_session()    # like .NET AgentSession

    async for chunk in agent.run("What's the weather and timezone for Seattle?",
                                 stream=True, session=session):
        if chunk.text:
            print(chunk.text, end="", flush=True)
```

`session = agent.create_session()` keeps client-side conversation state and history. Pass the same `session` on every `agent.run(...)` to preserve context across turns; the server still sees the full message history because `Agent` forwards it.

## The seven AG-UI features

The integration covers all seven canonical AG-UI features. Each is a small pattern on top of the same primitives:

| # | Feature | Pattern |
| --- | --- | --- |
| 1 | **Agentic chat** | Plain `Agent`; emit streaming text |
| 2 | **Backend tool rendering** | Server-side `@tool`; results stream as `ToolCallResultEvent` to the UI |
| 3 | **Human-in-the-loop** | `@tool(approval_mode="always_require")` — endpoint emits an approval request, client supplies the decision |
| 4 | **Agentic generative UI** | Long-running async `@tool` that streams progress via `Content` updates |
| 5 | **Tool-based generative UI** | Return `state_update(text=..., tool_result={...})` so the UI renders a custom component |
| 6 | **Shared state** | `AgentFrameworkAgent(agent, state_schema=..., predict_state_config=...)` — bidirectional sync via `StateSnapshotEvent` / `StateDeltaEvent` |
| 7 | **Predictive state updates** | `predict_state_config={"field": {"tool": "...", "tool_argument": "..."}}` — streams tool args as optimistic state updates |

## Tool return helpers — `state_update`

When a server-side tool needs to send **different** payloads to the model, the UI, and shared state, return a `state_update(...)`:

```python
from agent_framework import Content, tool
from agent_framework.ag_ui import state_update


@tool
async def get_weather(city: str) -> Content:
    data = await fetch_weather(city)
    return state_update(
        text=f"{city}: {data['temp']}°C and {data['conditions']}",  # → LLM tool result
        tool_result={                                                # → AG-UI ToolCallResultEvent
            "component": "weather-card",
            "city": city,
            "temperature": data["temp"],
            "conditions": data["conditions"],
            "humidity": data["humidity"],
        },
        state={"weather": {"city": city, **data}},                   # → merged into shared state
    )
```

- `text` is what the LLM consumes (so it can reason on the result).
- `tool_result` is the structured payload the front-end renders (custom card, chart, etc.).
- `state` is merged into AG-UI's durable shared state — clients see it via `StateSnapshotEvent` / `StateDeltaEvent`.

## Authentication

The endpoint is open by default. For production, pass FastAPI dependencies:

```python
import os
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from agent_framework.ag_ui import add_agent_framework_fastapi_endpoint

API_KEY_HEADER  = APIKeyHeader(name="X-API-Key", auto_error=False)
EXPECTED_KEY    = os.environ.get("AG_UI_API_KEY")

async def verify_api_key(api_key: str | None = Security(API_KEY_HEADER)) -> None:
    if not EXPECTED_KEY:
        return                                              # dev-mode: warn-only
    if not api_key:
        raise HTTPException(401, "Missing API key.")
    if api_key != EXPECTED_KEY:
        raise HTTPException(403, "Invalid API key.")

add_agent_framework_fastapi_endpoint(
    app, agent, "/",
    dependencies=[Depends(verify_api_key)],
)
```

The `dependencies=` list accepts any FastAPI `Depends(...)` — OAuth 2.0 (`OAuth2PasswordBearer`), JWT (`python-jose`), Microsoft Entra ID (`azure-identity`), per-IP rate limits, or your own.

## Methods (quick reference)

| Symbol | Purpose |
| --- | --- |
| `add_agent_framework_fastapi_endpoint(app, target, path, *, dependencies=None, ...)` | Mount AG-UI on a FastAPI app; `target` is `Agent`, `Workflow`, `AgentFrameworkAgent`, or `AgentFrameworkWorkflow` |
| `AGUIChatClient(endpoint=..., headers=None, ...)` | `BaseChatClient` that speaks AG-UI; use as `async with` |
| `AGUIChatClient.get_response(messages, *, stream, tools=None, metadata=None, options=None)` | Send chat to the server; `metadata={"thread_id": ...}` continues a thread |
| `AgentFrameworkAgent(agent, *, name=None, description=None, state_schema=None, predict_state_config=None, require_confirmation=False, orchestrators=None)` | Wraps an `Agent` for advanced AG-UI features (shared state, predictive updates, custom orchestrators) |
| `AgentFrameworkWorkflow(workflow=None, *, workflow_factory=None, name=None)` | Wraps a `Workflow`; pass `workflow_factory` for per-thread instances |
| `state_update(*, text, tool_result=None, state=None)` | Tool return helper that targets LLM / UI / shared state separately |

## Complete Example — hybrid hosted agent

**`server.py`**

```python
import os
from agent_framework import Agent, tool
from agent_framework.openai import OpenAIChatCompletionClient
from agent_framework.ag_ui import add_agent_framework_fastapi_endpoint
from fastapi import FastAPI


@tool(description="Get the time zone for a location.")
def get_time_zone(location: str) -> str:
    timezones = {
        "seattle": "Pacific Time (UTC-8)",
        "new york": "Eastern Time (UTC-5)",
        "london": "Greenwich Mean Time (UTC+0)",
    }
    return timezones.get(location.lower(), f"No timezone data for {location}")


agent = Agent(
    name="AGUIAssistant",
    instructions="Use get_weather for weather and get_time_zone for time zones.",
    client=OpenAIChatCompletionClient(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        model=os.environ["AZURE_OPENAI_MODEL"],
    ),
    tools=[get_time_zone],                  # server-side only
)

app = FastAPI(title="AG-UI Server")
add_agent_framework_fastapi_endpoint(app, agent, "/")
# uvicorn server:app --host 127.0.0.1 --port 5100
```

**`client.py`**

```python
import asyncio
import os
from agent_framework import Agent, tool
from agent_framework.ag_ui import AGUIChatClient


@tool(description="Get the current weather for a location.")
def get_weather(location: str) -> str:
    weather = {"seattle": "Rainy, 55°F", "london": "Cloudy, 52°F"}
    return weather.get(location.lower(), f"No weather data for {location}")


async def main() -> None:
    server_url = os.environ.get("AGUI_SERVER_URL", "http://127.0.0.1:5100/")
    async with AGUIChatClient(endpoint=server_url) as remote:
        agent = Agent(
            name="remote_assistant",
            instructions="You are a helpful assistant.",
            client=remote,
            tools=[get_weather],            # client-side only
        )
        session = agent.create_session()

        for question in [
            "I live in Seattle. What's the weather and what time zone am I in?",
            "Now compare that to London.",
        ]:
            print(f"\nUser: {question}\nAssistant: ", end="", flush=True)
            async for chunk in agent.run(question, stream=True, session=session):
                if chunk.text:
                    print(chunk.text, end="", flush=True)
            print()


asyncio.run(main())
```

The server LLM transparently calls `get_weather` (executed on the client) and `get_time_zone` (executed on the server) in the same turn.

## Conventions

- **One agent / workflow per endpoint path.** Mount additional ones with different paths.
- **Server tools and client tools are disjoint.** Never register the same `@tool` on both sides — pick the side that owns the implementation.
- **Drive client-side tool calls through `Agent`,** not raw `AGUIChatClient`. The function-invocation mixin is on `Agent`.
- **Send `thread_id` on every follow-up call.** For raw client usage, capture it from `update.additional_properties["thread_id"]` on the first response; for `Agent` usage, the same `session` keeps things consistent.
- **Use `AgentFrameworkWorkflow(workflow_factory=...)`** when the workflow carries per-conversation state (request_info, accumulators, super-step buffers).
- **Use `state_update(...)`** when a tool's UI rendering needs more structure than its text result.
- **Guard production endpoints** with `dependencies=[Depends(...)]` — the default is unauthenticated.
- Event types on the wire are `UPPERCASE_WITH_UNDERSCORES` (`RUN_STARTED`, `RUN_FINISHED`) and field names are `camelCase` (`threadId`, `availableInterrupts`). The Python adapters handle the mapping; only matters if you write raw protocol code.

## Best Practices

- Reuse one `AGUIChatClient` instance across multiple calls — it owns an HTTP pool. Create per-conversation sessions on the wrapping `Agent` instead of new clients.
- For long-running tools (Feature 4 — agentic generative UI), make them `async` and yield interim `Content` updates so the UI sees progress.
- For Feature 7 (predictive state), match `tool_argument` exactly to the argument name on your `@tool` — that's how the integration knows what to stream into state.
- Authenticate with `azure-identity`'s `DefaultAzureCredential` in deployed environments; fall back to `AZURE_OPENAI_API_KEY` only for local dev.
- For browser UIs, AG-UI Dojo / CopilotKit clients can speak directly to your endpoint — register the well-known paths (`/agentic_chat`, `/backend_tool_rendering`, etc.) used by the examples package if you want drop-in compatibility.
- Wrap problematic calls with explicit timeouts on `httpx` client init (`AGUIChatClient(endpoint=..., timeout=60.0)`) — the protocol is streaming, so default per-read timeouts may need tuning.

## Reference Files

| File | Topic |
| --- | --- |
| [references/server.md](references/server.md) | Hosting an `Agent`, FastAPI wiring, server-side tools, authentication |
| [references/client.md](references/client.md) | `AGUIChatClient` direct use, streaming, non-streaming, thread continuity |
| [references/agent_integration.md](references/agent_integration.md) | `Agent` + `AGUIChatClient` hybrid pattern, `AgentSession`, multi-turn |
| [references/workflows.md](references/workflows.md) | Hosting `Workflow`s, thread-scoped workflows, `AgentFrameworkWorkflow` |
| [references/features.md](references/features.md) | All 7 AG-UI features, `state_update`, predictive state, HITL approval |
