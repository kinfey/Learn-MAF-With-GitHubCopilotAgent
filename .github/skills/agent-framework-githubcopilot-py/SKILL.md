---
name: agent-framework-githubcopilot-py
description: Build local GitHub Copilot–backed agents using the Microsoft Agent Framework Python SDK (agent-framework-github-copilot). Use when creating agents with GitHubCopilotAgent that delegate to the GitHub Copilot CLI, configuring permission handlers (shell, read, write, url, mcp), managing Copilot sessions for multi-turn conversations, registering local/HTTP MCP servers, applying instruction directories, enforcing function-tool approval, and streaming responses. Covers function tools, runtime option overrides, and multi-permission workflows.
license: MIT
metadata:
  author: Microsoft
  version: "1.0.0"
  package: agent-framework-github-copilot
---

# Agent Framework GitHub Copilot Agents

Build local agents backed by the GitHub Copilot CLI using the Microsoft Agent Framework Python SDK. `GitHubCopilotAgent` spawns and talks to the `copilot` CLI on the user's machine — there is no Azure endpoint and no cloud credential to configure. Permissions, sessions, and MCP servers are managed by the CLI; this SDK gives you a Pythonic, async-first interface on top.

## Architecture

```
User Query →
  GitHubCopilotAgent (Python) → GitHub Copilot CLI (local process)
                            ↓
              agent.run() / agent.run(..., stream=True)
                            ↓
   Tools: Function tools | Built-in actions (shell/read/write/url) | MCP servers
                            ↓
            Permission handler (on_permission_request)
                            ↓
              Session (multi-turn conversation persistence)
```

## Installation

```bash
# Full framework (recommended)
pip install agent-framework --pre

# Or GitHub Copilot package only
pip install agent-framework-github-copilot --pre
```

## Prerequisites

1. **GitHub Copilot CLI** — install and authenticate (`copilot auth`).
2. **Active GitHub Copilot subscription** — required for the CLI to call models.
3. **Python 3.10+** with the package above installed.

## Environment Variables

All are optional. Configure them when you need to override defaults:

```bash
export GITHUB_COPILOT_CLI_PATH="copilot"        # Path to the Copilot CLI executable
export GITHUB_COPILOT_MODEL="gpt-5"              # e.g. "gpt-5", "claude-sonnet-4"; server default otherwise
export GITHUB_COPILOT_TIMEOUT="60"               # Request timeout in seconds
export GITHUB_COPILOT_LOG_LEVEL="info"           # CLI log level
export GITHUB_COPILOT_COPILOT_HOME="~/.copilot"  # Directory for CLI session state and config
```

## Lifecycle & Permissions

> **🔑 Two rules apply to every code sample below:**
>
> 1. **Always wrap the agent in `async with`.** It owns a child Copilot CLI process; the context manager guarantees it is started, drained, and terminated cleanly.
> 2. **Permissions are deny-by-default.** Built-in capabilities (shell, read, write, url, mcp) are gated by the CLI. To allow them, install an `on_permission_request` handler on `default_options`. Function tools decorated with `approval_mode="always_require"` are independently gated by `on_function_approval`.

```python
from agent_framework.github import GitHubCopilotAgent
from copilot.generated.session_events import PermissionRequest
from copilot.session import PermissionRequestResult


def prompt_permission(request: PermissionRequest, context: dict[str, str]) -> PermissionRequestResult:
    """Prompt the user to approve a Copilot CLI permission request."""
    print(f"[Permission: {request.kind}]")
    if request.full_command_text is not None:
        print(f"  Command: {request.full_command_text}")
    if request.path is not None:
        print(f"  Path: {request.path}")
    if request.url is not None:
        print(f"  URL: {request.url}")
    response = input("Approve? (y/n): ").strip().lower()
    if response in ("y", "yes"):
        return PermissionRequestResult(kind="approved")
    return PermissionRequestResult(kind="denied-interactively-by-user")
```

`PermissionRequest.kind` is one of: `"shell"`, `"read"`, `"write"`, `"url"`, `"mcp"`. The same handler can gate any subset; just inspect `kind` and approve selectively. **Only enable the permissions you actually need.**

## Core Workflow

### Basic Agent

```python
import asyncio
from agent_framework.github import GitHubCopilotAgent


async def main() -> None:
    agent = GitHubCopilotAgent(
        instructions="You are a helpful assistant.",
    )
    async with agent:
        result = await agent.run("Hello!")
        print(result)


asyncio.run(main())
```

### Agent with Function Tools

```python
from random import randint
from typing import Annotated

from agent_framework import tool
from agent_framework.github import GitHubCopilotAgent
from pydantic import Field


# approval_mode="never_require" is safe for read-only helpers; use
# "always_require" for anything with side effects and pair with on_function_approval.
@tool(approval_mode="never_require")
def get_weather(
    location: Annotated[str, Field(description="The location to get the weather for.")],
) -> str:
    """Get the weather for a given location."""
    conditions = ["sunny", "cloudy", "rainy", "stormy"]
    return f"The weather in {location} is {conditions[randint(0, 3)]} with a high of {randint(10, 30)}°C."


async def main() -> None:
    agent = GitHubCopilotAgent(
        instructions="You are a helpful weather agent.",
        tools=[get_weather],
    )
    async with agent:
        result = await agent.run("What's the weather in Seattle?")
        print(result)
```

### Enabling Built-In Capabilities (Shell / Read / Write / URL)

Built-in actions are unlocked simply by attaching a permission handler. The agent decides when to call them.

```python
from agent_framework.github import GitHubCopilotAgent
from copilot.generated.session_events import PermissionRequest
from copilot.session import PermissionRequestResult


def approve_reads_only(request: PermissionRequest, context: dict[str, str]) -> PermissionRequestResult:
    if request.kind == "read":
        return PermissionRequestResult(kind="approved")
    return PermissionRequestResult(kind="denied-interactively-by-user")


async def main() -> None:
    agent = GitHubCopilotAgent(
        instructions="You can read project files to answer questions.",
        default_options={"on_permission_request": approve_reads_only},
    )
    async with agent:
        result = await agent.run("Read README.md and summarize it.")
        print(result)
```

### Streaming Responses

```python
async def main() -> None:
    agent = GitHubCopilotAgent(instructions="You are a helpful assistant.")
    async with agent:
        print("Agent: ", end="", flush=True)
        async for chunk in agent.run("Tell me a short story", stream=True):
            if chunk.text:
                print(chunk.text, end="", flush=True)
        print()
```

### Multi-Turn Conversations with Sessions

```python
async def main() -> None:
    agent = GitHubCopilotAgent(instructions="You are a helpful weather agent.")
    async with agent:
        session = agent.create_session()

        result1 = await agent.run("What's the weather in Tokyo?", session=session)
        print(result1)

        # Same session → context is preserved
        result2 = await agent.run("How about London?", session=session)
        print(result2)

        # The session ID can be saved and reused later
        saved_id = session.service_session_id
```

### MCP Servers (Local + Remote)

```python
from copilot.session import MCPServerConfig

mcp_servers: dict[str, MCPServerConfig] = {
    "filesystem": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
        "tools": ["*"],
    },
    "microsoft-learn": {
        "type": "http",
        "url": "https://learn.microsoft.com/api/mcp",
        "tools": ["*"],
    },
}

agent = GitHubCopilotAgent(
    instructions="You can use the local filesystem and Microsoft Learn.",
    default_options={
        "on_permission_request": prompt_permission,
        "mcp_servers": mcp_servers,
    },
)
```

## Agent Methods

| Method | Description |
|--------|-------------|
| `agent.run(query, ...)` | Run a single turn; returns the final response (or an async iterator when `stream=True`). |
| `agent.run(query, stream=True)` | Stream chunks as they are produced. |
| `agent.create_session()` | Create a fresh Copilot session for multi-turn context. |
| `agent.get_session(service_session_id=...)` | Resume an existing session by its server-side ID. |
| `async with agent:` | Required — manages the underlying CLI subprocess lifecycle. |

## Default Options Quick Reference

Set on `GitHubCopilotAgent(default_options={...})`. Any key can be overridden per-call via `agent.run(..., options={...})`.

| Key | Purpose |
|-----|---------|
| `on_permission_request` | Callback that approves/denies CLI permission prompts (`shell`, `read`, `write`, `url`, `mcp`). |
| `on_function_approval` | Callback that approves/denies function-tool calls marked `approval_mode="always_require"`. Receives a `FunctionCallContent`, returns `bool` (sync or async). |
| `instruction_directories` | List of directories with custom instruction files the CLI loads for the session. |
| `mcp_servers` | Dict of MCP server configs (`type: "stdio"` or `"http"`). |
| `system_message` | Runtime override: `{"mode": "replace" \| "append", "content": "..."}`. |
| `timeout` | Per-call timeout in seconds (overrides `GITHUB_COPILOT_TIMEOUT`). |

## Complete Example

```python
import asyncio
from random import randint
from typing import Annotated

from agent_framework import tool
from agent_framework.github import GitHubCopilotAgent
from copilot.generated.session_events import PermissionRequest
from copilot.session import MCPServerConfig, PermissionRequestResult
from pydantic import Field


@tool(approval_mode="never_require")
def get_weather(
    location: Annotated[str, Field(description="City name")],
) -> str:
    """Get weather for a location."""
    conditions = ["sunny", "cloudy", "rainy", "stormy"]
    return f"Weather in {location}: {conditions[randint(0, 3)]}, {randint(10, 30)}°C."


def prompt_permission(request: PermissionRequest, context: dict[str, str]) -> PermissionRequestResult:
    print(f"[Permission: {request.kind}]")
    response = input("Approve? (y/n): ").strip().lower()
    if response in ("y", "yes"):
        return PermissionRequestResult(kind="approved")
    return PermissionRequestResult(kind="denied-interactively-by-user")


async def main() -> None:
    mcp_servers: dict[str, MCPServerConfig] = {
        "microsoft-learn": {
            "type": "http",
            "url": "https://learn.microsoft.com/api/mcp",
            "tools": ["*"],
        },
    }

    agent = GitHubCopilotAgent(
        instructions="You are a research assistant with multiple capabilities.",
        tools=[get_weather],
        default_options={
            "on_permission_request": prompt_permission,
            "mcp_servers": mcp_servers,
        },
    )

    async with agent:
        session = agent.create_session()

        # Non-streaming
        result = await agent.run(
            "Look up Azure Functions Python on Microsoft Learn and summarize.",
            session=session,
            options={"timeout": 120},
        )
        print(f"Response: {result}")

        # Streaming with the same session
        print("\nStreaming: ", end="")
        async for chunk in agent.run("Now compare it to Container Apps.", session=session, stream=True):
            if chunk.text:
                print(chunk.text, end="", flush=True)
        print()


if __name__ == "__main__":
    asyncio.run(main())
```

## Conventions

- Always use `async with agent:` — the CLI subprocess must be cleaned up.
- Pass functions decorated with `@tool(...)` directly to `tools=[...]`.
- Use `Annotated[type, Field(description=...)]` for function parameter docs.
- Use `agent.create_session()` for multi-turn conversations; save `session.service_session_id` to resume later via `agent.get_session(...)`.
- Approve only the `PermissionRequest.kind` values your workload requires; deny everything else.
- Mark side-effecting function tools `approval_mode="always_require"` and pair them with `on_function_approval`.
- Configure MCP servers via the `mcp_servers` dict; do **not** import `MCPStreamableHTTPTool` / `HostedMCPTool` (those belong to other providers).

## Best Practices

1. **Async-first.** All handlers, callbacks, and `agent.run` calls are async. `on_function_approval` may be sync or async.
2. **Least privilege.** Each `PermissionRequest.kind` you approve grants the agent real access to the host. Approve narrowly (per-kind, or per-call by inspecting `request.full_command_text` / `request.path` / `request.url`).
3. **Persist sessions explicitly.** Capture `session.service_session_id` after a run to resume the same conversation later — sessions are not implicitly re-used across `agent.run()` calls without passing `session=`.
4. **Override at runtime, not on the class.** Use `agent.run(..., options={...})` to vary `system_message`, `instruction_directories`, `mcp_servers`, or `timeout` for a single call instead of constructing a new agent.
5. **Enable observability when debugging.** `configure_otel_providers(enable_console_exporters=True)` from `agent_framework.observability` adds OpenTelemetry tracing around every CLI round-trip.

## Reference Files

- [references/permissions.md](references/permissions.md): Permission handler patterns for shell, read, write, url, and mcp.
- [references/sessions.md](references/sessions.md): Session creation, persistence, and resumption.
- [references/mcp.md](references/mcp.md): MCP server configuration (stdio + HTTP) for the Copilot CLI.
- [references/advanced.md](references/advanced.md): Function approval, instruction directories, runtime overrides, streaming details, and observability.
