# Advanced Patterns Reference

Advanced patterns for `GitHubCopilotAgent`: function-tool approval, instruction directories, runtime overrides, streaming details, observability, and error handling.

## Function Tool Approval

For function tools that have side effects, mark them `approval_mode="always_require"` and provide an `on_function_approval` callback. Unlike `on_permission_request` (which gates the CLI's built-in actions), `on_function_approval` gates calls to your `@tool`-decorated functions.

If `on_function_approval` is **not** configured, calls to `always_require` tools are denied by default and the model is told why — so it can apologize or try a different approach.

### Synchronous Approval

```python
import asyncio
from random import randrange
from typing import Annotated

from agent_framework import Content, tool
from agent_framework.github import GitHubCopilotAgent


@tool(approval_mode="always_require")
def get_weather_detail(
    location: Annotated[str, "The city and state, e.g. San Francisco, CA"],
) -> str:
    """Get a detailed weather report for a location."""
    conditions = ["sunny", "cloudy", "rainy", "stormy"]
    return (
        f"The weather in {location} is {conditions[randrange(0, len(conditions))]} "
        f"with a high of {randrange(10, 30)}C and humidity of 88%."
    )


def prompt_for_approval(call: Content) -> bool:
    """Sync approval prompt — receives a FunctionCallContent."""
    print(f"\n[Function Approval Request]")
    print(f"  Tool: {call.name}")
    print(f"  Arguments: {call.arguments}")
    response = input("Approve this tool call? (y/n): ").strip().lower()
    return response in ("y", "yes")


async def main() -> None:
    agent = GitHubCopilotAgent(
        instructions="You are a helpful weather assistant.",
        tools=[get_weather_detail],
        default_options={"on_function_approval": prompt_for_approval},
    )
    async with agent:
        result = await agent.run("Give me the detailed weather for Seattle.")
        print(result)


asyncio.run(main())
```

### Asynchronous Approval

Use an `async` callback when the approval involves I/O (HTTP review service, UI queue, DB lookup). Wrap `input()` with `asyncio.to_thread` so the event loop is not blocked.

```python
async def prompt_for_approval_async(call: Content) -> bool:
    print(f"\n[Function Approval - async]\n  Tool: {call.name}\n  Arguments: {call.arguments}")
    response = await asyncio.to_thread(input, "Approve this tool call? (y/n): ")
    return response.strip().lower() in ("y", "yes")


agent = GitHubCopilotAgent(
    instructions="You are a helpful weather assistant.",
    tools=[get_weather_detail],
    default_options={"on_function_approval": prompt_for_approval_async},
)
```

### Deny-by-Default

```python
# No on_function_approval configured → always_require tools are denied,
# and the model receives an explanatory tool error so it can adjust.
agent = GitHubCopilotAgent(
    instructions="You are a helpful weather assistant.",
    tools=[get_weather_detail],
)
async with agent:
    result = await agent.run("Give me the detailed weather for Paris.")
    print(result)   # Agent will apologize / suggest a different approach
```

### When to Use Which Callback

| Callback | Gates | Receives | Returns |
|----------|-------|----------|---------|
| `on_permission_request` | Built-in CLI actions: `shell`, `read`, `write`, `url`, `mcp` | `PermissionRequest` | `PermissionRequestResult` |
| `on_function_approval` | Agent-framework `@tool` calls marked `approval_mode="always_require"` | `FunctionCallContent` (a `Content`) | `bool` (sync or async) |

---

## Instruction Directories

Instruction directories let the CLI load project-specific or team-shared instruction files alongside its built-in instructions. They are configured via the `instruction_directories` key in `default_options` (or per-call via `options=`).

### Default Instruction Directories

```python
from pathlib import Path

from agent_framework.github import GitHubCopilotAgent


project_root = Path.cwd()
instruction_dirs = [
    str(project_root / ".copilot" / "instructions"),
    str(project_root / "docs" / "agent-guidelines"),
]

agent = GitHubCopilotAgent(
    instructions="You are a helpful coding assistant.",
    default_options={
        "on_permission_request": prompt_permission,
        "instruction_directories": instruction_dirs,
    },
)

async with agent:
    result = await agent.run("Summarize the coding conventions I should follow.")
    print(result)
```

### Runtime Override

Runtime `options` take precedence for that single call. Use this to swap in project-specific or team-shared instructions on the fly.

```python
agent = GitHubCopilotAgent(
    instructions="You are a helpful assistant.",
    default_options={
        "on_permission_request": prompt_permission,
        "instruction_directories": ["/team/shared/instructions"],
    },
)

async with agent:
    # Uses the default directories
    result1 = await agent.run("What instructions are you following?")

    # Overrides for this call only
    result2 = await agent.run(
        "Now what instructions are you following?",
        options={"instruction_directories": ["/project/specific/instructions"]},
    )
```

---

## Runtime System Message Override

Override the system message for a single call via `options={"system_message": ...}`. Modes:

- `"replace"` — replace the instructions for this call.
- `"append"` — append to the existing instructions for this call.

```python
agent = GitHubCopilotAgent(
    instructions="Always respond in exactly 3 words.",
    tools=[get_weather],
    default_options={"on_permission_request": prompt_permission},
)

async with agent:
    # Uses the default instructions (3-word responses)
    result1 = await agent.run("What's the weather in Paris?")
    print(result1)

    # Replace for this call only — get a detailed answer
    result2 = await agent.run(
        "What's the weather in Paris?",
        options={
            "system_message": {
                "mode": "replace",
                "content": (
                    "You are a weather expert. Provide detailed weather "
                    "information with temperature and recommendations."
                ),
            },
        },
    )
    print(result2)
```

---

## Streaming Responses

`agent.run(..., stream=True)` returns an async iterator of chunks. Each chunk has a `.text` attribute (may be empty for non-text events).

```python
agent = GitHubCopilotAgent(instructions="You are a helpful weather agent.")

async with agent:
    print("Agent: ", end="", flush=True)
    async for chunk in agent.run("What's the weather in Tokyo?", stream=True):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    print()
```

Streaming works the same way with `session=` for multi-turn conversations.

---

## Observability with OpenTelemetry

`GitHubCopilotAgent` has OpenTelemetry tracing built in. Call `configure_otel_providers()` **before** constructing the agent.

```python
from agent_framework.github import GitHubCopilotAgent
from agent_framework.observability import configure_otel_providers


configure_otel_providers(enable_console_exporters=True)

async def main() -> None:
    async with GitHubCopilotAgent(instructions="Say hello.") as agent:
        result = await agent.run("Hello!")
        print(result)
```

For OTLP / Azure Monitor / file exporters, see the observability samples in the agent-framework repo.

---

## Configuring Timeouts

Two layers:

```bash
# Default for every call
export GITHUB_COPILOT_TIMEOUT=60
```

```python
# Per-call override
result = await agent.run(
    "Search Microsoft Learn for Azure Functions Python and summarize",
    options={"timeout": 120},
)
```

Increase the timeout for remote MCP calls, long shell commands, or large file operations.

---

## Error Handling Patterns

### Graceful Degradation

```python
async def run_with_fallback(agent, query: str, session=None) -> str:
    try:
        return await agent.run(query, session=session)
    except Exception as e:
        print(f"Agent run failed: {e}")
        # Fall back to an agent with no built-in capabilities enabled
        fallback = GitHubCopilotAgent(
            instructions="Answer based on your knowledge only — no tools.",
        )
        async with fallback:
            return f"[Fallback] {await fallback.run(query)}"
```

### Retry with Exponential Backoff

```python
import asyncio


async def run_with_retry(agent, query: str, session=None, max_retries: int = 3) -> str | None:
    for attempt in range(max_retries):
        try:
            return await agent.run(query, session=session)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt
            print(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
            await asyncio.sleep(wait_time)
    return None
```

---

## Performance: Reuse the Agent

The agent owns a Copilot CLI subprocess. **Construct it once and reuse it** for multiple calls — don't spin up a new `async with GitHubCopilotAgent(...)` block per request.

```python
# ✅ Good: one agent, many calls
agent = GitHubCopilotAgent(instructions="Answer questions concisely.")
async with agent:
    for query in queries:
        result = await agent.run(query)
        print(result)

# ❌ Bad: process churn on every call
for query in queries:
    async with GitHubCopilotAgent(instructions="...") as agent:
        await agent.run(query)
```

For independent conversations within the same agent, give each one its own session:

```python
async def handle(agent, query: str) -> str:
    session = agent.create_session()
    return await agent.run(query, session=session)


results = await asyncio.gather(*(handle(agent, q) for q in queries))
```

---

## Debugging

Increase CLI log verbosity via the environment:

```bash
export GITHUB_COPILOT_LOG_LEVEL=debug
```

Enable Python logging for the SDK:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("agent_framework").setLevel(logging.DEBUG)
```

Inspect streaming chunks (text + tool events):

```python
async for chunk in agent.run("Calculate something", stream=True):
    print(f"[DEBUG] chunk type={type(chunk).__name__} text={chunk.text!r}")
```
